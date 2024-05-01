import sys

sys.path.append("..")

import asyncio
import base64
import binascii
import hashlib
import json
import time
from typing import Annotated, Optional

import hruid
import redis
from dotenv import load_dotenv
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    status,
)
import math
from sqlalchemy import or_, and_
from fastapi_limiter.depends import RateLimiter
from pydantic import BaseModel
from sqlalchemy.orm import Session
import copy
from pathlib import Path
from humanfriendly import format_timespan

import models
from database import SessionLocal, engine
from routers.auth import TokenData, get_current_user
from routers.content import add_presigned_single, allTags
from script_utils.util import *
from utils import CLOUDFLARE_METADATA, CLOUDFLARE_CONTENT, IMAGE_MODELS, MODEL_COMPUTE
from utils import remove_key, sql_dict, job_presigned_get
import replicate
from routers.reindex_job import reindex_image_job
from routers.upload import generate_new_filename, index_media_task

load_dotenv()


router = APIRouter(
    prefix="/jobs", tags=["jobs"], responses={404: {"description": "Not found"}}
)

models.Base.metadata.create_all(bind=engine)


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


def get_redis():
    try:
        rd = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
        yield rd
    finally:
        rd.close()


db_dependency = Annotated[Session, Depends(get_db)]


class RegisterJobModel(BaseModel):
    job_type: str
    config_json: dict

class UploadJobModel(BaseModel):
    filename: str
    md5: str
    filesize: int
    job_id: int
    key: str
    is_srt: Optional[bool] = False
    is_zip: Optional[bool] = False

class IndexContent(BaseModel):
    config: dict
    processtype: str
    md5: str
    key: str
    job_id: int

class JobStatus(BaseModel):
    job_id: int 
    job_key: str

class JobEstimate(BaseModel):
    content_id: int 
    job_config: dict
    

def create_content_entry(config: dict, db: Session, user_id: int, job_id: int):
    try:
        content_detail = (
            db.query(models.Content)
            .filter(
                models.Content.id == config["config_json"]["job_data"]["content_id"]
            )
            .filter(models.Content.user_id == user_id)
            .filter(models.Content.status == "completed")
            .filter(models.Content.content_type == config["job_type"])
            .first()
        )
        main_id = None
        r_tags = []
        if content_detail.id_related == None:
            main_id = content_detail.id
        else:
            main_id = content_detail.id_related
            related_tags = (
                db.query(models.ContentTags)
                .filter(models.ContentTags.content_id == content_detail.id)
                .all()
            )
            r_tags = [x.tag_id for x in related_tags]
        if content_detail is None:
            raise HTTPException(status_code=400, detail="Content not found")
        if content_detail.user_id != user_id:
            raise HTTPException(status_code=400, detail="Content not found")
        all_tags = allTags()
        tags = [
            all_tags[x]["id"]
            for x in config["config_json"]["job_data"]["filters"].keys()
            if config["config_json"]["job_data"]["filters"][x]["active"] == True
        ]
        tags.extend(x for x in r_tags if x not in tags)
        if 14 in tags:
            create_content_model = models.Content(
                user_id=user_id,
                title=str(content_detail.title).rsplit('.',1)[:-1][0] + ".srt",
                thumbnail="srt_thumbnail.jpg",
                id_related=main_id,
                job_id = job_id,
                created_at=int(time.time()),
                status="processing",
                content_type=content_detail.content_type,
            )
            db.add(create_content_model)
            db.commit()
            db.refresh(create_content_model)
            db.add(
                models.ContentTags(
                    content_id=create_content_model.id,
                    tag_id=14,
                    created_at=int(time.time()),
                )
            )
            db.commit()
            tags.remove(14)
        if 12 in tags and config["job_type"] == "audio":
            create_content_model = models.Content(
                user_id=user_id,
                title=str(content_detail.title).rsplit('.',1)[:-1][0] + ".zip",
                thumbnail="stem.jpg",
                id_related=main_id,
                job_id = job_id,
                created_at=int(time.time()),
                status="processing",
                content_type=content_detail.content_type,
            )
            db.add(create_content_model)
            db.commit()
            db.refresh(create_content_model)
            db.add(
                models.ContentTags(
                    content_id=create_content_model.id,
                    tag_id=12,
                    created_at=int(time.time()),
                )
            )
            db.commit()
            tags.remove(12)
        content_title = Path(content_detail.title).stem
        if len(tags) != 0: 
            create_content_model = models.Content(
                user_id=user_id,
                title=content_title,
                thumbnail=content_detail.thumbnail,
                id_related=main_id,
                job_id = job_id,
                created_at=int(time.time()),
                status="processing",
                content_type=content_detail.content_type,
            )
            db.add(create_content_model)
            db.commit()
            db.refresh(create_content_model)
            for tag in tags:
                db.add(
                    models.ContentTags(
                        content_id=create_content_model.id,
                        tag_id=tag,
                        created_at=int(time.time()),
                    )
                )
                db.commit()
        return create_content_model.id
    except Exception as e:
        raise HTTPException(status_code=400, detail="Unable to create content entry")


@celeryapp.task(name="routers.jobs.image_process")
def image_process_task(job_config: dict):
    try:
        db = SessionLocal()
        main_content = (
            db.query(models.Content)
            .filter(
                models.Content.id == job_config["config_json"]["job_data"]["content_id"]
            )
            .filter(models.Content.user_id == job_config["user_id"])
            .filter(models.Content.status == "completed")
            .filter(models.Content.content_type == job_config["job_type"])
            .first()
        )
        if main_content is None:
            raise Exception("Content not found")
        content_url = job_presigned_get(main_content.link, CLOUDFLARE_CONTENT)
        copy_content_url = copy.copy(content_url)
        for filter_ in job_config["config_json"]["job_data"]["filters"]:
            model_config = job_config["config_json"]["job_data"]["filters"][filter_]
            if model_config["active"]:
                params = {
                    "seed": 1999,
                    "image": content_url
                }
                model_tag = IMAGE_MODELS[filter_]["model"]
                if "params" in IMAGE_MODELS[filter_].keys():
                    for x in IMAGE_MODELS[filter_]["params"]:
                        params[x] = model_config[IMAGE_MODELS[filter_]["params"][x]]
                content_url = replicate.run(
                    model_tag ,
                    input = params
                )
        if copy_content_url != content_url:
            result = reindex_image_job(job_config, content_url=content_url)
        db.close()
    except Exception as e:
        db = SessionLocal()
        content = (
            db.query(models.Content)
            .filter(
                models.Content.id == job_config["content_id"]
            )
            .filter(models.Content.user_id == job_config["user_id"])
            .filter(models.Content.content_type == job_config["job_type"])
            .first()
        )
        content.status = "failed"
        content.updated_at = int(time.time())
        job = (
            db.query(models.Jobs)
            .filter(models.Jobs.job_id == content.job_id)
            .first()
        )
        job.job_status = "Failed"
        job.job_process = "error"
        db.add(job)
        db.add(content)
        db.commit()
        db.close()
        return {"detail": "Failed", "data": str(e)}


@router.post(
    "/register_job", dependencies=[Depends(RateLimiter(times=120, seconds=60))]
)
async def register_job(
    job_dict: RegisterJobModel,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    try:
        generator = hruid.Generator()
        phrase = generator.random()
        user_details = (
            db.query(models.Users)
            .filter(models.Users.id == current_user.user_id)
            .first()
        )
        running_jobs = (
            db.query(models.Content)
            .filter(models.Content.user_id == current_user.user_id)
            .filter(models.Content.status == "processing")
            .count()
        )
        if running_jobs >= USER_TIER[user_details.user_tier]["max_jobs"]:
            raise HTTPException(
                status_code=400,
                detail="You have reached your maximum active jobs. Please wait for them to complete.",
            )
        create_job_model = models.Jobs(
            user_id=current_user.user_id,
            job_name=phrase,
            job_type=job_dict.job_type,
            job_status="Processing",
            job_tier=user_details.user_tier,
            created_at=int(time.time()),
            job_key=True,
            config_json=json.dumps(job_dict.config_json),
            job_process="started",
            key=hashlib.md5(generator.random().encode()).hexdigest(),
        )
        db.add(create_job_model)
        db.commit()
        db.refresh(create_job_model)
        content_id = create_content_entry(job_dict.dict(), db, current_user.user_id, create_job_model.job_id)
        create_job_model.content_id = content_id
        db.add(create_job_model)
        db.commit()
        job_config = sql_dict(create_job_model)
        remove_key(job_config, "_sa_instance_state")
        job_config['config_json'] = json.loads(job_config['config_json'])
        if job_dict.job_type == "video":
            # To Do
            pass
        if job_dict.job_type == "image":
            celery_process = image_process_task.delay(job_config)
            create_job_model.celery_id = celery_process.id
            db.commit()
        if job_dict.job_type == "audio":
            # To Do
            pass
        return {"detail": "Success", "data": "Job registered successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail="Unable to register job")


def fetch_content_data(content_id: int, db: Session):
    try:
        content_detail = (
            db.query(models.Content)
            .filter(models.Content.id == content_id)
            .first()
        )
        if content_detail is None:
            raise HTTPException(status_code=400, detail="Content not found")
        return content_detail
    except Exception as e:
        raise HTTPException(status_code=400, detail="Unable to fetch content data")


@router.get("/fetch_jobs")
async def fetch_jobs(
    job_id: int,
    key: str,
    db: Session = Depends(get_db),
    rd: redis.Redis = Depends(get_redis),
):
    try:
        job_detail = (
            db.query(models.Jobs)
            .filter(models.Jobs.job_id == job_id)
            .filter(models.Jobs.key == key)
            .first()
        )
        if job_detail is None:
            raise HTTPException(status_code=400, detail="Job not found")
        job_config = {}
        content_detail = fetch_content_data(
            job_detail.content_id, db
        )
        main_content = fetch_content_data(
            content_detail.id_related, db
        ).__dict__
        job_config["content"] = add_presigned_single(
            main_content["link"], CLOUDFLARE_CONTENT, None
        )
        job_config["title"] = main_content["title"]
        job_config["job"] = json.loads(job_detail.config_json)
        return {"detail": "Success", "data": job_config}
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=400, detail="Unable to fetch job details")


@router.get("/active_jobs", dependencies=[Depends(RateLimiter(times=120, seconds=60))])
async def active_jobs(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
    rd: redis.Redis = Depends(get_redis),
):
    try:
        all_tags = allTags(id=True)
        job_details = (
            db.query(models.Jobs)
            .filter(models.Jobs.user_id == current_user.user_id)
            .filter(or_(
                    models.Jobs.job_status == "Processing",
                    models.Jobs.job_status == "Loading",
                ))
            .all()
        )
        job_details = [x.__dict__ for x in job_details]
        remove_keys = [
            "celery_id",
            "_sa_instance_state",
            "user_id",
            "config_json",
            "key",
            "job_key",
            "job_tier",
            "updated_at",
        ]
        for x in job_details:
            for y in remove_keys:
                x.pop(y)
        final_data = []
        for job in job_details:
            content_detail = fetch_content_data(
                job["content_id"], db
            ).__dict__
            content_detail.pop("_sa_instance_state")
            content_detail = {k: v for k, v in content_detail.items() if v is not None}
            content_detail["thumbnail"] = add_presigned_single(
                content_detail["thumbnail"], CLOUDFLARE_METADATA, rd
            )
            if content_detail["status"].value != "processing":
                continue
            job["content_detail"] = content_detail
            all_content_tags = []
            related_content = (
                db.query(models.Content)
                .filter(models.Content.job_id == job["job_id"])
                .all()
            )
            all_content_id = [x.id for x in related_content]
            tags_query = (
                db.query(models.ContentTags)
                .filter(models.ContentTags.content_id.in_(all_content_id))
                .all()
            )
            for y in tags_query:
                all_content_tags.append(y.tag_id)
            job["content_detail"]["tags"] = []
            for tag in all_content_tags:
                job["content_detail"]["tags"].append((all_tags[str(tag)]["readable"]))
            job["content_detail"]["tags"] = ",".join(job["content_detail"]["tags"])
            final_data.append(job)
        return {"detail": "Success", "data": final_data}
    except Exception as e:
        raise HTTPException(status_code=400, detail="Unable to fetch jobs")


@router.get(
    "/past_jobs",
    dependencies=[Depends(RateLimiter(times=120, seconds=60))],
    status_code=status.HTTP_200_OK,
)
async def past_jobs(
    limit: int,
    offset: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
    rd: redis.Redis = Depends(get_redis),
):
    try:
        all_tags = allTags(id=True)
        if limit > 5:
            raise HTTPException(
                status_code=400, detail="Limit cannot be greater than 5"
            )
        query = (
            db.query(models.Jobs)
            .join(models.Content, models.Jobs.content_id == models.Content.id)
            .filter(models.Content.status != "processing")
            .filter(models.Jobs.user_id == current_user.user_id)
            .order_by(models.Jobs.created_at.asc())
            .limit(limit)
            .offset(offset)
            .all()
        )
        total_count = (
            db.query(models.Jobs)
            .join(models.Content, models.Jobs.content_id == models.Content.id)
            .filter(models.Content.status != "processing")
            .filter(models.Jobs.user_id == current_user.user_id)
            .count()
        )
        job_details = [x.__dict__ for x in query]
        remove_keys = [
            "_sa_instance_state",
            "user_id",
            "config_json",
            "key",
            "job_key",
            "job_tier"
        ]
        for x in job_details:
            for y in remove_keys:
                x.pop(y)
        final_data = []
        for job in job_details:
            content_detail = fetch_content_data(
                job["content_id"], db
            ).__dict__
            content_detail.pop("_sa_instance_state")
            content_detail = {k: v for k, v in content_detail.items() if v is not None}
            content_detail["thumbnail"] = add_presigned_single(
                content_detail["thumbnail"], CLOUDFLARE_METADATA, rd
            )
            job["content_detail"] = content_detail
            tags_query = (
                db.query(models.ContentTags)
                .filter(models.ContentTags.content_id == int(job["content_id"]))
                .all()
            )
            all_content_tags = []
            for y in tags_query:
                all_content_tags.append(y.tag_id)
            job["content_detail"]["tags"] = []
            for tag in all_content_tags:
                job["content_detail"]["tags"].append((all_tags[str(tag)]["readable"]))
            job["content_detail"]["tags"] = ",".join(job["content_detail"]["tags"])
            final_data.append(job)
        return {"detail": "Success", "data": final_data, "total": total_count}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    await websocket.accept()
    data = await websocket.receive_json()
    current_user = get_current_user(db, data["token"])
    if "id" not in data:
        await websocket.send_json({"detail": "Failed", "data": "Invalid request"})
        return
    try:
        while True:
            result = {}
            for id in data["id"]:
                job_status = (
                    db.query(models.Jobs)
                    .filter(models.Jobs.job_id == id)
                    .filter(models.Jobs.user_id == current_user.user_id)
                    .first()
                )
                if job_status is None:
                    result[id] = "Not found"
                    continue
                result[id] = job_status.job_status
            await websocket.send_json({"detail": "Success", "data": result})
            await asyncio.sleep(30)
    except WebSocketDisconnect:
        await websocket.close()
        return
    except Exception:
        await websocket.close()
        return


@router.get("/filter_config")
async def filter_config(
    current_user: TokenData = Depends(get_current_user), db: Session = Depends(get_db)
):
    user_details = (
        db.query(models.Users).filter(models.Users.id == current_user.user_id).first()
    )
    if user_details is None:
        raise HTTPException(status_code=400, detail="User not found")
    return {
        "detail": "Success",
        "data": json.dumps(MODELS_CONFIG),  # noqa: F405
        "tier_config": json.dumps(USER_TIER),
        "tier": user_details.user_tier,
    }


def generate_signed_url_task(uploaddict: dict, db: Session):
    try:
        job_detail = (
            db.query(models.Jobs)
            .filter(models.Jobs.job_id == uploaddict["job_id"])
            .filter(models.Jobs.key == uploaddict["key"])
            .first()
        ) 
        if job_detail is None:
            return {"detail": "Failed", "data": "Job Not Found"}
        unique_filename = generate_new_filename(uploaddict["filename"])
        key_file = f"{job_detail.user_id}/{unique_filename}"
        content_md5 = base64.b64encode(binascii.unhexlify(uploaddict["md5"])).decode(
            "utf-8"
        )
        response = r2_client.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": os.getenv("BUCKET_NAME", CLOUDFLARE_CONTENT),
                "Key": key_file,
                "ContentMD5": content_md5,
            },
            ExpiresIn=int(os.getenv("EXPIRE_TIME", 3600)),
        )
        update_contents = (
            db.query(models.Content)
            .filter(models.Content.job_id == job_detail.job_id)
            .all()
        )
        update_content = None
        if uploaddict["is_srt"]:
            for x in update_contents:
                if x.title.endswith(".srt"):
                    update_content = x
                    break 
        elif uploaddict["is_zip"]:
            for x in update_contents:
                if x.title.endswith(".zip"):
                    update_content = x
                    break 
        else:
            for x in update_contents:
                if x.title.endswith(".srt") == False and x.title.endswith(".zip") == False:
                    update_content = x
                    break
        update_content.link = key_file
        update_content.md5 = content_md5
        update_content.updated_at = int(time.time())
        db.add(update_content)
        db.commit()
        return {
                "detail": "Success",
                "data": {
                    "signed_url": response,
                    "filename": unique_filename,
                    "md5": content_md5,
                    "id": update_content.id,
                },
            }
    except Exception as e:
        return {"detail": "Failed", "data": "Filetype not supported"}

@router.post(
    "/generate_presigned_post",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimiter(times=20, seconds=60))],
)
async def generate_url(
    upload: UploadJobModel,
    db: Session = Depends(get_db),
):
    result = generate_signed_url_task(upload.dict(), db)
    if result["detail"] == "Failed":
        if "Storage limit exceeded" in result["data"]:
            raise HTTPException(status_code=507, detail=result["data"])
        raise HTTPException(status_code=400, detail=result["data"])
    return result

@router.post(
    "/reindexfile",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimiter(times=20, seconds=60))],
)
async def file_index(
    indexdata: IndexContent,
    db: Session = Depends(get_db),
):
    job_info = (
        db.query(models.Jobs)
        .filter(models.Jobs.job_id == indexdata.job_id)
        .filter(models.Jobs.key == indexdata.key)
        .first()
    )
    if job_info is None:
        raise HTTPException(status_code=400, detail="Job not found")
    content_data = (
        db.query(models.Content)
        .filter(models.Content.id == indexdata.config["id"])
        .filter(models.Content.user_id == job_info.user_id)
        .first()
    )
    if content_data is None:
        logger.error(
            f"Invalid content id in job reindex - {indexdata.config['id']}"
        )
        raise HTTPException(status_code=400, detail="Invalid content id")
    if indexdata.processtype not in ["video", "audio", "subtitle", "zip"]:
        logger.error(f"Invalid processtype for in job reindex")
        raise HTTPException(status_code=400, detail="Invalid processtype")
    result = index_media_task.delay(indexdata.dict(), job_info.user_id, True)
    content_data.status = "indexing"
    content_data.content_type = indexdata.processtype
    db.add(content_data)
    db.commit()
    logger.info(f"File indexed with celery id {result.id}")
    return {"detail": "Success", "data": {result.id}}

def roundup(x):
    return int(math.ceil(x / 100.0)) * 100

@router.post(
    "/job_status",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimiter(times=20, seconds=60))],
)
async def job_status(
    job_status: JobStatus,
    db: Session = Depends(get_db)
):
    try:
        job = (
            db.query(models.Jobs)
            .filter(models.Jobs.job_id == job_status.job_id)
            .filter(models.Jobs.key == job_status.job_key)
            .first()
        )
        if job is None:
            raise HTTPException(status_code=400, detail="Job not found")
        content_data = (
            db.query(models.Content)
            .filter(models.Content.job_id == job_status.job_id)
            .all()
        )
        status = "completed"
        for x in content_data:
            if str(x.status) == "completed":
                x.updated_at = int(time.time())
                db.add(x)
            else:
                status = "failed"
        job.job_status = status.capitalize()
        job.job_process = status.lower()
        job.updated_at = int(time.time())
        job.job_key = False
        db.add(job)
        db.commit()
        return HTTPException(status_code=200, detail="Job updated")
    except Exception as e:
        logger.error(f"Error while job indexing - {job_status}")
        logger.error(f"Error - {str(e)}")
        return HTTPException(status_code=400, detail="Error in Job Indexing")
    
@router.post(
    "/get_estimate",\
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(times=240, seconds=60))],
)
async def get_estimate(
    job_config: JobEstimate, 
    db: Session = Depends(get_db), 
    current_user: TokenData = Depends(get_current_user)):
    content = (
        db.query(models.Content)
        .filter(models.Content.id == job_config.content_id)
        .filter(models.Content.user_id == current_user.user_id)
        .first()
    )
    if content is None:
        raise HTTPException(status_code=400, detail="Content Not Found")
    if content.content_type == "video":
        filters = dict(job_config.job_config)
        resolution = content.resolution
        fps = np.ceil(float(content.fps))
        duration = content.duration
        width, height = map(int, resolution.split("x"))
        duration_seconds = duration_to_seconds(duration)
        total_pixels = width * height * fps * duration_seconds
        total_time = 0
        for filter_name, filter_config in filters.items():
            if filter_config["active"]:
                if isinstance(MODEL_COMPUTE["video"][filter_name], dict):
                    if "model" in filter_config:
                        model_name = filter_config["model"]
                    if "factor" in filter_config:
                        model_name = filter_config["factor"]["name"]
                    pixels_per_second = MODEL_COMPUTE["video"][filter_name][model_name]
                else:
                    pixels_per_second = MODEL_COMPUTE["video"][filter_name]
                filter_time = total_pixels / pixels_per_second
                total_time += filter_time 
        total_time = roundup(np.ceil(total_time) + 300 + 600)
        per_second_cost = 0.0003
        estimate = total_time * per_second_cost
        estimate = format(max(round(estimate, 2), 0.05),".2f")
        return {"detail": "Success", "eta": format_timespan(total_time, max_units=2), "price": estimate}
    if content.content_type == "image":
        filters = dict(job_config.job_config)
        resolution = content.resolution
        width, height = map(int, resolution.split("x"))
        scale = 1
        if width > 1080:
            scale = 2
        total_time = 0
        for filter_name, filter_config in filters.items():
            if filter_config["active"]:
                if isinstance(MODEL_COMPUTE["image"][filter_name], dict):
                    if "model" in filter_config:
                        model_name = filter_config["model"]
                    compute_time = MODEL_COMPUTE["image"][filter_name][model_name] * scale + 30
                else:
                    compute_time = MODEL_COMPUTE["image"][filter_name] * scale + 30
                total_time += compute_time
        total_time = roundup(np.ceil(total_time) + 5 + 30)
        per_second_cost = 0.000725
        estimate = total_time * per_second_cost
        estimate = format(max(round(estimate, 2), 0.05),".2f")
        return {"detail": "Success", "eta": format_timespan(total_time, max_units=2), "price": estimate}
    if content.content_type == "audio":
        filters = dict(job_config.job_config)
        duration = content.duration
        duration_seconds = duration_to_seconds(duration)
        total_time = 0
        for filter_name, filter_config in filters.items():
            if filter_config["active"]:
                compute_per_seconds = MODEL_COMPUTE["audio"][filter_name]
                filter_time = int(np.ceil(duration_seconds / compute_per_seconds))
                total_time += filter_time
        total_time = roundup(np.ceil(total_time) + 30 + 600)
        per_second_cost = 0.0003
        estimate = total_time * per_second_cost
        estimate = format(max(round(estimate, 2), 0.05),".2f")
        return {"detail": "Success", "eta": format_timespan(total_time, max_units=2), "price": estimate}
    return 0.00

    