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
import ast
import shutil
import binascii
from utils import throttler

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


def create_pre_upload_data(file_type, user_id, unique_filename, content_md5):
    model = {
        "video": models.Videos,
        "audio": models.Audios,
        "image": models.Images,
    }.get(file_type, None)

    if model:
        return model(
            user_id=user_id,
            title=unique_filename,
            link=f"{user_id}/{unique_filename}",
            tags="original",
            md5=content_md5,
            status="pending",
            created_at=int(time.time()),
        )
    else:
        return None


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
    preUploadData = create_pre_upload_data(
        file_type, user_id, unique_filename, content_md5
    )

    if preUploadData:
        db.add(preUploadData)
        db.commit()
        return {
            "detail": "Success",
            "data": {
                "signed_url": response,
                "filename": unique_filename,
                "md5": content_md5,
            },
        }
    else:
        return {"detail": "Failed", "data": "Filetype not supported"}


@router.post("/generate_presigned_post", status_code=status.HTTP_201_CREATED)
async def generate_url(
    upload: UploadDict,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if throttler.consume(identifier="user_id") == False:
        raise HTTPException(status_code=429, detail="Too Many Requests")
    result = generate_signed_url_task(upload.dict(), current_user.user_id, db)
    if result["detail"] == "Failed":
        if "Storage limit exceeded" in result["data"]:
            raise HTTPException(status_code=507, detail=result["data"])
        raise HTTPException(status_code=400, detail=result["data"])
    return result


def video_indexing(response, thumbnail_path, key_file, db, indexdata):
    try:
        video_data = is_video_valid(response)
        if video_data == False:
            return {"detail": "Failed", "data": "Video is not valid"}
        vidData = video_fetch_data(video_data)
        create_thumbnail(response, thumbnail_path, vidData["time_offset"])
        lower_resolution(thumbnail_path)
        thumbnail_upload(thumbnail_path)
        videoData = (
            db.query(models.Videos).filter(models.Videos.link == key_file).first()
        )
        videoData.duration = convert_seconds(int(float(vidData["duration"])))
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


def image_indexing(response, thumbnail_path, key_file, db, indexdata):
    try:
        img_size, width, height = lower_resolution_image(response, thumbnail_path)
        create_thumbnail_image(thumbnail_path)
        thumbnail_upload(thumbnail_path)
        imageData = (
            db.query(models.Images).filter(models.Images.link == key_file).first()
        )
        imageData.size = int(img_size)
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


def audio_indexing(response, thumbnail_path, key_file, db, indexdata):
    try:
        audio_data = audio_image(
            response, indexdata["config"]["filename"].split(".")[-1], thumbnail_path
        )
        if audio_data == False:
            return {"detail": "Failed", "data": "Audio is not valid"}
        thumbnail_upload(thumbnail_path)
        audioData = (
            db.query(models.Audios).filter(models.Audios.link == key_file).first()
        )
        audioData.duration = convert_seconds(
            int(float(audio_data["format"]["duration"]))
        )
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
            ExpiresIn=60,
        )
        s3.close()
        if indexdata["processtype"] == "video":
            result = video_indexing(response, thumbnail_path, key_file, db, indexdata)
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
            result = image_indexing(response, thumbnail_path, key_file, db, indexdata)
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
            result = audio_indexing(response, thumbnail_path, key_file, db, indexdata)
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
        print(str(e))
        return {"detail": "Failed", "data": "Invalid processtype"}


@router.post("/indexfile", status_code=status.HTTP_201_CREATED)
async def file_index(
    indexdata: IndexContent,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if throttler.consume(identifier="user_id") == False:
        raise HTTPException(status_code=429, detail="Too Many Requests")
    if indexdata.processtype not in ["video", "audio", "image"]:
        raise HTTPException(status_code=400, detail="Invalid processtype")
    result = index_media_task(indexdata.dict(), current_user.user_id, db)
    if result["detail"] == "Failed":
        raise HTTPException(status_code=400, detail=result["data"])
    return HTTPException(status_code=201, detail="File indexed")
