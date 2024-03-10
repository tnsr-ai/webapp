import base64
import json
import sys

sys.path.append("..")
import time
from typing import Optional, Annotated
from fastapi import Depends, HTTPException, APIRouter, status
import models
import os
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from pydantic import BaseModel
import boto3
import re
import uuid
from utils import *
from routers.auth import get_current_user, TokenData
import models
from script_utils.util import *
from dotenv import load_dotenv
from fastapi_limiter.depends import RateLimiter
import ast
import shutil
import binascii
from utils import logger
from routers.content import allTags
from utils import r2_resource, r2_client, logger, delete_r2_file
from utils import USER_TIER, STORAGE_LIMITS

load_dotenv()


router = APIRouter(
    prefix="/upload", tags=["upload"], responses={404: {"description": "Not allowed"}}
)

models.Base.metadata.create_all(bind=engine)

os.makedirs("thumbnail", exist_ok=True)


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


class UploadDict(BaseModel):
    filename: str
    filetype: str
    md5: str
    filesize: int


class Upload(BaseModel):
    signed_url: str
    filename: str


class IndexContent(BaseModel):
    config: dict
    processtype: str
    md5: str
    id_related: Optional[int] = None


def get_user_data(db, user_id: int):
    return db.query(models.Users).filter(models.Users.id == user_id).first()


def get_user_dashboard(db, user_id: int):
    return (
        db.query(models.Dashboard).filter(models.Dashboard.user_id == user_id).first()
    )


def create_pre_upload_data(file_type, user_id, filename, unique_filename, content_md5):
    return models.Content(
        user_id=user_id,
        title=filename,
        link=f"{user_id}/{unique_filename}",
        md5=content_md5,
        status="processing",
        created_at=int(time.time()),
    )


def generate_new_filename(filename):
    unique_identifier = str(uuid.uuid4())
    basename, extension = os.path.splitext(filename)
    basename = re.sub(r"\W+", "", basename)
    new_filename = f"{basename}_{unique_identifier}{extension}"
    return new_filename


def generate_signed_url_task(uploaddict: dict, user_id: int, db: Session):
    user_data = get_user_data(db, user_id)
    if not user_data.verified:
        return {"detail": "Failed", "data": "User not verified"}

    user_dashboard = get_user_dashboard(db, user_id)
    if (
        user_dashboard
        and user_dashboard.storage_limit - user_dashboard.storage_used
        < uploaddict["filesize"]
    ):
        return {"detail": "Failed", "data": "Storage limit exceeded"}

    unique_filename = generate_new_filename(uploaddict["filename"])
    key_file = f"{user_id}/{unique_filename}"
    content_md5 = base64.b64encode(binascii.unhexlify(uploaddict["md5"])).decode(
        "utf-8"
    )

    response = r2_client.generate_presigned_url(
        ClientMethod="put_object",
        Params={
            "Bucket": os.getenv("BUCKET_NAME", CLOUDFLARE_CONTENT),
            "Key": key_file,
            "ContentType": uploaddict["filetype"],
            "ContentMD5": content_md5,
        },
        ExpiresIn=int(os.getenv("EXPIRE_TIME", 3600)),
    )

    file_type = uploaddict["filetype"].split("/")[0]
    filename = uploaddict["filename"]
    preUploadData = create_pre_upload_data(
        file_type, user_id, filename, unique_filename, content_md5
    )
    if preUploadData:
        db.add(preUploadData)
        db.commit()
        db.refresh(preUploadData)
        all_tags = allTags()
        tags_association = models.ContentTags(
            content_id=preUploadData.id,
            tag_id=all_tags["original"]["id"],
            created_at=int(time.time()),
        )
        db.add(tags_association)
        db.commit()
        return {
            "detail": "Success",
            "data": {
                "signed_url": response,
                "filename": unique_filename,
                "md5": content_md5,
                "id": preUploadData.id,
            },
        }
    else:
        return {"detail": "Failed", "data": "Filetype not supported"}


@router.post(
    "/generate_presigned_post",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimiter(times=20, seconds=60))],
)
async def generate_url(
    upload: UploadDict,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = generate_signed_url_task(upload.dict(), current_user.user_id, db)
    if result["detail"] == "Failed":
        logger.error(f"Failed to generate presigned url for {current_user.user_id}")
        if "Storage limit exceeded" in result["data"]:
            logger.error(f"Storage limit exceeded for {current_user.user_id}")
            raise HTTPException(status_code=507, detail=result["data"])
        logger.error(f"Failed to generate presigned url for {current_user.user_id}")
        raise HTTPException(status_code=400, detail=result["data"])
    logger.info(f"Presigned url generated for {current_user.user_id}")
    return result


def video_indexing(response, thumbnail_path, db, indexdata, user_tier):
    try:
        video_data = is_video_valid(response)
        if video_data == False:
            return {"detail": "Failed", "data": "Video is not valid"}
        vidData = video_fetch_data(video_data)
        allowed_config = USER_TIER[user_tier]["video"]
        if (
            vidData["width"] > allowed_config["width"]
            or vidData["height"] > allowed_config["height"]
        ):
            return {
                "detail": "Failed",
                "data": f"Resolution is too large for {user_tier} tier",
            }
        allowed_duration = allowed_config["duration"]
        if float(allowed_config["duration"]) == -1:
            allowed_duration = float("inf")
        if float(vidData["duration"]) > allowed_duration:
            return {
                "detail": "Failed",
                "data": f"Video duration is too long for {user_tier} tier",
            }
        create_thumbnail(response, thumbnail_path, vidData["time_offset"])
        lower_resolution(thumbnail_path)
        thumbnail_upload(thumbnail_path)
        videoData = (
            db.query(models.Content)
            .filter(models.Content.id == indexdata["config"]["id"])
            .first()
        )
        videoData.duration = convert_seconds(int(float(vidData["duration"])))
        videoData.content_type = "video"
        videoData.size = int(vidData["filesize"])
        videoData.fps = vidData["frame_rate"]
        videoData.resolution = f"{vidData['width']}x{vidData['height']}"
        videoData.thumbnail = thumbnail_path
        videoData.md5 = indexdata["md5"]
        videoData.status = "completed"
        if indexdata["id_related"] is not None:
            videoData.id_related = indexdata["id_related"]
        videoData.updated_at = int(time.time())
        return {"detail": "Success", "data": videoData}
    except Exception as e:
        return {"detail": "Failed", "data": str(e)}


def image_indexing(response, thumbnail_path, db, indexdata, user_tier):
    try:
        img_size, width, height = lower_resolution_image(response, thumbnail_path)
        allowed_config = USER_TIER[user_tier]["image"]
        if width > allowed_config["width"] or height > allowed_config["height"]:
            return {
                "detail": "Failed",
                "data": f"Image resolution is too large for {user_tier} tier",
            }
        create_thumbnail_image(thumbnail_path)
        thumbnail_upload(thumbnail_path)
        imageData = (
            db.query(models.Content)
            .filter(models.Content.id == indexdata["config"]["id"])
            .first()
        )
        imageData.size = int(img_size)
        imageData.content_type = "image"
        imageData.resolution = f"{width}x{height}"
        imageData.thumbnail = thumbnail_path
        imageData.md5 = indexdata["md5"]
        imageData.status = "completed"
        if indexdata["id_related"] is not None:
            imageData.id_related = indexdata["id_related"]
        imageData.updated_at = int(time.time())
        return {"detail": "Success", "data": imageData}
    except Exception as e:
        return {"detail": "Failed", "data": str(e)}


def audio_indexing(response, thumbnail_path, db, indexdata, user_tier):
    try:
        audio_data = audio_image(
            response, indexdata["config"]["filename"].split(".")[-1], thumbnail_path
        )
        allowed_config = USER_TIER[user_tier]["audio"]
        allowed_duration = allowed_config["duration"]
        if float(allowed_config["duration"]) == -1:
            allowed_duration = float("inf")
        if float(audio_data["format"]["duration"]) > float(allowed_duration):
            return {
                "detail": "Failed",
                "data": f"Audio duration is too long for {user_tier} tier",
            }
        if audio_data == False:
            return {"detail": "Failed", "data": f"Audio is not valid"}
        thumbnail_upload(thumbnail_path)
        audioData = (
            db.query(models.Content)
            .filter(models.Content.id == indexdata["config"]["id"])
            .first()
        )
        audioData.duration = convert_seconds(
            int(float(audio_data["format"]["duration"]))
        )
        audioData.content_type = "audio"
        audioData.size = int(audio_data["format"]["size"])
        audioData.hz = audio_data["streams"][0]["sample_rate"]
        audioData.thumbnail = thumbnail_path
        audioData.md5 = indexdata["md5"]
        if indexdata["id_related"] is not None:
            audioData.id_related = indexdata["id_related"]
        audioData.status = "completed"
        audioData.updated_at = int(time.time())
        return {"detail": "Success", "data": audioData}
    except Exception as e:
        return {"detail": "Failed", "data": str(e)}


def index_media_task(indexdata: dict, user_id: int, db: Session):
    try:
        user = db.query(models.Users).filter(models.Users.id == user_id).first()
        user_data = db.query(models.Users).filter(models.Users.id == user_id).first()
        user_dashboard = (
            db.query(models.Dashboard)
            .filter(models.Dashboard.user_id == user_id)
            .first()
        )
        if user_data.verified == False:
            return {"detail": "Failed", "data": "User not verified"}
        info = indexdata["config"]
        indexfilename = info["indexfilename"]
        pathlib.Path(f"thumbnail/{user_id}").mkdir(parents=True, exist_ok=True)
        thumbnail_path = f"thumbnail/{user_id}/{os.path.splitext(indexfilename)[0]}.jpg"
        s3 = boto3.client(
            "s3",
            aws_access_key_id=CLOUDFLARE_ACCESS_KEY,
            aws_secret_access_key=CLOUDFLARE_SECRET_KEY,
            endpoint_url=CLOUDFLARE_ACCOUNT_ENDPOINT,
            config=botocore.config.Config(
                s3={"addressing_style": "path"},
                signature_version="s3v4",
                retries=dict(max_attempts=3),
            ),
        )
        key_file = f"{user_id}/{indexfilename}"
        obj_data = s3.head_object(Bucket=CLOUDFLARE_CONTENT, Key=key_file)
        if user_dashboard is not None:
            if int(user_dashboard.storage_limit) - int(
                user_dashboard.storage_used
            ) < int(obj_data["ContentLength"]):
                return {"detail": "Failed", "data": "Storage limit exceeded"}
        response = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": CLOUDFLARE_CONTENT, "Key": key_file},
            ExpiresIn=3600,
        )
        s3.close()
        if indexdata["processtype"] == "video":
            result = video_indexing(
                response, thumbnail_path, db, indexdata, user.user_tier
            )
            if result["detail"] == "Failed":
                return result
            videoData = result["data"]
            user_stats = (
                db.query(models.Dashboard)
                .filter(models.Dashboard.user_id == user_id)
                .first()
            )
            user_stats.video_processed += 1
            user_stats.uploads += int(videoData.size)
            user_stats.storage_used += int(videoData.size)
            storage_json = ast.literal_eval(user_stats.storage_json)
            storage_json["video"] = float(bytes_to_mb(videoData.size)) + float(
                storage_json["video"]
            )
            user_stats.storage_json = json.dumps(storage_json)
            db.add(user_stats)
            db.add(videoData)
            db.commit()
            shutil.rmtree(f"thumbnail/{user_id}")
            return {"detail": "Success", "data": "Video indexed"}
        if indexdata["processtype"] == "image":
            result = image_indexing(
                response, thumbnail_path, db, indexdata, user.user_tier
            )
            if result["detail"] == "Failed":
                return result
            imageData = result["data"]
            user_stats = (
                db.query(models.Dashboard)
                .filter(models.Dashboard.user_id == user_id)
                .first()
            )
            user_stats.image_processed += 1
            user_stats.uploads += int(imageData.size)
            user_stats.storage_used += int(imageData.size)
            storage_json = ast.literal_eval(user_stats.storage_json)
            storage_json["image"] = float(bytes_to_mb(imageData.size)) + float(
                storage_json["image"]
            )
            user_stats.storage_json = json.dumps(storage_json)
            db.add(user_stats)
            db.add(imageData)
            db.commit()
            shutil.rmtree(f"thumbnail/{user_id}")
            return {"detail": "Success", "data": "Image indexed"}
        if indexdata["processtype"] == "audio":
            result = audio_indexing(
                response, thumbnail_path, db, indexdata, user.user_tier
            )
            if result["detail"] == "Failed":
                return result
            audioData = result["data"]
            user_stats = (
                db.query(models.Dashboard)
                .filter(models.Dashboard.user_id == user_id)
                .first()
            )
            user_stats.audio_processed += 1
            user_stats.uploads += int(audioData.size)
            user_stats.storage_used += int(audioData.size)
            storage_json = ast.literal_eval(user_stats.storage_json)
            storage_json["audio"] = float(bytes_to_mb(audioData.size)) + float(
                storage_json["audio"]
            )
            user_stats.storage_json = json.dumps(storage_json)
            db.add(user_stats)
            db.add(audioData)
            db.commit()
            shutil.rmtree(f"thumbnail/{user_id}")
            return {"detail": "Success", "data": "Audio indexed"}
    except Exception as e:
        return {"detail": "Failed", "data": "Invalid processtype"}


@router.post(
    "/indexfile",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimiter(times=20, seconds=60))],
)
async def file_index(
    indexdata: IndexContent,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    content_data = (
        db.query(models.Content)
        .filter(models.Content.id == indexdata.config["id"])
        .first()
    )
    if content_data is None:
        logger.error(
            f"Invalid content id for {current_user.user_id} - {indexdata.config['id']}"
        )
        raise HTTPException(status_code=400, detail="Invalid content id")
    if indexdata.processtype not in ["video", "audio", "image"]:
        delete_r2_file(content_data.link, CLOUDFLARE_CONTENT)
        all_tags = (
            db.query(models.ContentTags)
            .filter(models.ContentTags.content_id == content_data.id)
            .all()
        )
        for tag in all_tags:
            db.delete(tag)
        db.delete(content_data)
        db.commit()
        logger.error(f"Invalid processtype for {current_user.user_id}")
        raise HTTPException(status_code=400, detail="Invalid processtype")
    result = index_media_task(indexdata.dict(), current_user.user_id, db)
    if result["detail"] == "Failed":
        delete_r2_file(content_data.link, CLOUDFLARE_CONTENT)
        all_tags = (
            db.query(models.ContentTags)
            .filter(models.ContentTags.content_id == content_data.id)
            .all()
        )
        for tag in all_tags:
            db.delete(tag)
        db.delete(content_data)
        db.commit()
        logger.error(f"Failed to index file for {current_user.user_id}")
        raise HTTPException(status_code=400, detail=result["data"])
    logger.info(f"File indexed for {current_user.user_id}")
    return HTTPException(status_code=201, detail="File indexed")
