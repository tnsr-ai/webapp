import sys

sys.path.append("..")

from typing import Optional
from fastapi import (
    Depends,
    HTTPException,
    APIRouter,
    WebSocketDisconnect,
    status,
    WebSocket,
)
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session
import sqlalchemy as sa
from sqlalchemy.orm import aliased
from pydantic import BaseModel, Field
from script_utils.util import *
from dotenv import load_dotenv
from typing import Optional, Annotated
import time
import json
import hruid
import hashlib
import redis
from celeryworker import celeryapp
from cryptography.fernet import Fernet
from routers.auth import authenticate_user, get_current_user, TokenData
from fastapi_limiter.depends import RateLimiter
from utils import CLOUDFLARE_METADATA
import asyncio
from routers.content import add_presigned_single, allTags

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


def create_content_entry(config: dict, db: Session, user_id: int):
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
        create_content_model = models.Content(
            user_id=user_id,
            title=content_detail.title,
            thumbnail=content_detail.thumbnail,
            id_related=content_detail.id,
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


# @celeryapp.task(name="routers.jobs.process_workers_demo")
# def process_media_celery():
#     try:
#         pass
#     except Exception as e:
#         return {"detail": "Failed", "data": str(e)}


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
            print("Max jobs reached")
            raise HTTPException(
                status_code=400,
                detail="You have reached your maximum active jobs. Please wait for them to complete.",
            )
        content_id = create_content_entry(job_dict.dict(), db, current_user.user_id)
        create_job_model = models.Jobs(
            user_id=current_user.user_id,
            content_id=content_id,
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
        # celery_process = process_media_celery.delay()
        # create_job_model.celery_id = celery_process.id
        # db.commit()
        return {"detail": "Success", "data": "Job registered successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail="Unable to register job")


def fetch_content_data(content_id: int, table: str, db: Session):
    try:
        content_detail = (
            db.query(models.Content)
            .filter(models.Content.id == content_id)
            .filter(models.Content.content_type == table)
            .first()
        )
        if content_detail is None:
            raise HTTPException(status_code=400, detail="Content not found")
        return content_detail
    except Exception as e:
        raise HTTPException(status_code=400, detail="Unable to fetch content data")


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
            .all()
        )
        job_details = [x.__dict__ for x in job_details]
        remove_keys = [
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
                job["content_id"], job["job_type"], db
            ).__dict__
            content_detail.pop("_sa_instance_state")
            content_detail = {k: v for k, v in content_detail.items() if v is not None}
            content_detail["thumbnail"] = add_presigned_single(
                content_detail["thumbnail"], CLOUDFLARE_METADATA, rd
            )
            if content_detail["status"].value != "processing":
                continue
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
            "job_tier",
            "updated_at",
        ]
        for x in job_details:
            for y in remove_keys:
                x.pop(y)
        final_data = []
        for job in job_details:
            content_detail = fetch_content_data(
                job["content_id"], job["job_type"], db
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
    except Exception as e:
        await websocket.close()
        return
