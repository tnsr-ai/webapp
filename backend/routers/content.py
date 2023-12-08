import sys

from script_utils.util import niceBytes

sys.path.append("..")

from typing import Optional
from fastapi import Depends, HTTPException, APIRouter, status
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import boto3, botocore
import redis
from celeryworker import celeryapp
from routers.auth import get_current_user, TokenData
import json
import re
from utils import (
    REDIS_HOST,
    REDIS_PORT,
    CLOUDFLARE_ACCESS_KEY,
    CLOUDFLARE_SECRET_KEY,
    CLOUDFLARE_ACCOUNT_ENDPOINT,
    CLOUDFLARE_EXPIRE_TIME,
    CLOUDFLARE_METADATA,
    CLOUDFLARE_CONTENT,
    CONTENT_EXPIRE,
)
from utils import throttler, remove_key


router = APIRouter(
    prefix="/content", tags=["content"], responses={404: {"description": "Not found"}}
)

models.Base.metadata.create_all(bind=engine)


def get_redis():
    try:
        rd = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
        yield rd
    finally:
        rd.close()


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


class ContentDict(BaseModel):
    limit: int
    offset: int
    content_type: str


def presigned_get(key, bucket, rd):
    try:
        if rd.exists(key):
            return rd.get(key).decode("utf-8")
        r2_client = boto3.client(
            "s3",
            aws_access_key_id=CLOUDFLARE_ACCESS_KEY,
            aws_secret_access_key=CLOUDFLARE_SECRET_KEY,
            endpoint_url=CLOUDFLARE_ACCOUNT_ENDPOINT + "/" + bucket,
            config=botocore.config.Config(
                s3={"addressing_style": "path"},
                signature_version="s3v4",
                retries=dict(max_attempts=3),
            ),
        )
        response = r2_client.generate_presigned_url(
            ClientMethod="get_object",
            Params={
                "Bucket": bucket,
                "Key": key,
            },
            ExpiresIn=CONTENT_EXPIRE,
        )
        rd.set(key, response)
        rd.expire(key, CONTENT_EXPIRE - 60)
        return response
    except Exception as e:
        return None


def add_presigned(data, key, result_key, bucket, rd):
    for x in data:
        x[result_key] = presigned_get(x[key], bucket, rd)
    return data


def add_presigned_single(file_key, bucket, rd):
    try:
        if rd.exists(file_key):
            return rd.get(file_key).decode("utf-8")
        r2_client = boto3.client(
            "s3",
            aws_access_key_id=CLOUDFLARE_ACCESS_KEY,
            aws_secret_access_key=CLOUDFLARE_SECRET_KEY,
            endpoint_url=CLOUDFLARE_ACCOUNT_ENDPOINT + "/" + bucket,
            config=botocore.config.Config(
                s3={"addressing_style": "path"},
                signature_version="s3v4",
                retries=dict(max_attempts=3),
            ),
        )
        response = r2_client.generate_presigned_url(
            ClientMethod="get_object",
            Params={
                "Bucket": bucket,
                "Key": file_key,
            },
            ExpiresIn=CONTENT_EXPIRE,
        )
        rd.set(file_key, response)
        rd.expire(file_key, CONTENT_EXPIRE - 60)
        return response
    except Exception as e:
        return None


def get_object_data(file_key, bucket, rd):
    try:
        redis_key = file_key + "_object"
        if rd.exists(redis_key):
            return json.loads(rd.get(redis_key).decode("utf-8"))
        r2_client = boto3.client(
            "s3",
            aws_access_key_id=CLOUDFLARE_ACCESS_KEY,
            aws_secret_access_key=CLOUDFLARE_SECRET_KEY,
            endpoint_url=CLOUDFLARE_ACCOUNT_ENDPOINT + "/" + bucket,
            config=botocore.config.Config(
                s3={"addressing_style": "path"},
                signature_version="s3v4",
                retries=dict(max_attempts=3),
            ),
        )
        response = r2_client.head_object(Bucket=bucket, Key=file_key)
        response = response["ResponseMetadata"]
        rd.set(redis_key, json.dumps(response))
        rd.expire(redis_key, CONTENT_EXPIRE - 60)
        return response
    except Exception as e:
        return None


def filter_data(data):
    delete_keys = [
        "user_id",
        "thumbnail",
        "md5",
        "id_related",
        "updated_at",
        "created_at",
    ]
    for x in data:
        for key in delete_keys:
            if key in x:
                del x[key]
        x["size"] = niceBytes(x["size"])
    return data


def get_content_table(user_id, table_name, limit, offset, db):
    try:
        tableName = {
            "video": models.Videos,
            "audio": models.Audios,
            "image": models.Images,
        }
        get_table = (
            db.query(tableName[table_name])
            .filter(tableName[table_name].user_id == user_id)
            .filter(tableName[table_name].id_related == None)
            .filter(tableName[table_name].status == "completed")
            .order_by(tableName[table_name].created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )
        user_data = db.query(models.Users).filter(models.Users.id == user_id).first()
        if user_data.verified == False:
            return {"detail": "Failed", "data": "User not verified"}
        all_result = [x.__dict__ for x in get_table]
        remove_key(all_result, "_sa_instance_state")
        get_counts = (
            db.query(tableName[table_name])
            .filter(tableName[table_name].user_id == user_id)
            .filter(tableName[table_name].id_related == None)
            .filter(tableName[table_name].status == "completed")
            .count()
        )
        return {"detail": "Success", "data": [all_result, get_counts]}
    except Exception as e:
        return {"detail": "Failed", "data": "Unable to fetch content"}


@router.get("/get_content", status_code=status.HTTP_200_OK)
async def generate_url(
    limit: int,
    offset: int,
    content_type: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
    rd: redis.Redis = Depends(get_redis),
):
    if throttler.consume(identifier="user_id") == False:
        raise HTTPException(status_code=429, detail="Too Many Requests")
    try:
        if limit > 12:
            raise HTTPException(status_code=400, detail="Limit cannot be more than 10")
        result_ = get_content_table(
            current_user.user_id, content_type, limit, offset, db
        )
        if result_["detail"] == "Failed":
            raise HTTPException(status_code=400, detail="Unable to fetch content")
        result_ = result_["data"]
        result = add_presigned(
            result_[0], "thumbnail", "thumbnail_link", CLOUDFLARE_METADATA, rd
        )
        result = filter_data(result)
        result = {"data": result, "detail": "Success", "total": result_[1]}
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Something went wrong"
        )


def get_content_list_celery(
    db: Session,
    content_id: int,
    content_type: str,
    user_id: int,
    limit: int = 5,
    offset: int = 0,
):
    try:
        tableName = {
            "video": models.Videos,
            "audio": models.Audios,
            "image": models.Images,
        }
        get_counts = (
            db.query(tableName[content_type])
            .filter(tableName[content_type].user_id == user_id)
            .filter(tableName[content_type].id_related == content_id)
            .count()
            + 1
        )
        get_main = (
            db.query(tableName[content_type])
            .filter(tableName[content_type].user_id == user_id)
            .filter(tableName[content_type].id == content_id)
            .first()
        )
        user_data = db.query(models.Users).filter(models.Users.id == user_id).first()
        if user_data.verified == False:
            return {"detail": "Failed", "data": "User not verified"}
        if get_main is None:
            return {"detail": "Failed", "data": "Unable to fetch content"}
        main_title = get_main.title
        if offset == 0:
            get_main = (
                db.query(tableName[content_type])
                .filter(tableName[content_type].user_id == user_id)
                .filter(tableName[content_type].id == content_id)
                .first()
            )
            if get_main is None:
                return {"detail": "Failed", "data": "Unable to fetch content"}
            get_related = (
                db.query(tableName[content_type])
                .filter(tableName[content_type].user_id == user_id)
                .filter(tableName[content_type].id_related == content_id)
                .order_by(tableName[content_type].created_at)
                .limit(limit - 1)
                .offset(offset)
                .all()
            )
            result = [get_main.__dict__]
            for x in get_related:
                result.append(x.__dict__)
            remove_key(result, "_sa_instance_state")
            return {
                "detail": "Success",
                "data": result,
                "total": get_counts,
                "title": main_title,
            }
        else:
            get_related = (
                db.query(tableName[content_type])
                .filter(tableName[content_type].user_id == user_id)
                .filter(tableName[content_type].id_related == content_id)
                .order_by(tableName[content_type].created_at)
                .limit(limit)
                .offset(offset - 1)
                .all()
            )
            result = []
            for x in get_related:
                result.append(x.__dict__)
            remove_key(result, "_sa_instance_state")
            return {
                "detail": "Success",
                "data": result,
                "total": get_counts,
                "title": main_title,
            }
    except Exception as e:
        return {"detail": "Failed", "data": "Unable to fetch content"}


@router.get("/get_content_list", status_code=status.HTTP_200_OK)
async def get_content_list(
    limit: int,
    offset: int,
    content_id: int,
    content_type: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
    rd: redis.Redis = Depends(get_redis),
):
    if throttler.consume(identifier="user_id") == False:
        raise HTTPException(status_code=429, detail="Too Many Requests")
    if limit > 5:
        raise HTTPException(status_code=400, detail="Limit cannot be more than 5")
    try:
        result = get_content_list_celery(
            db, content_id, content_type, current_user.user_id, limit, offset
        )
        if result["detail"] == "Failed":
            raise HTTPException(status_code=400, detail="Unable to fetch content")
        if len(result["data"]) == 0:
            raise HTTPException(status_code=400, detail="No more content")
        result["data"] = add_presigned(
            result["data"], "thumbnail", "thumbnail_link", CLOUDFLARE_METADATA, rd
        )
        result["data"] = add_presigned(
            result["data"], "link", "content_link", CLOUDFLARE_CONTENT, rd
        )
        result["data"] = filter_data(result["data"])
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Something went wrong"
        )


def download_content_task(
    user_id: int, content_id: int, content_type: str, db: Session, rd: redis.Redis
):
    try:
        tableName = {
            "video": models.Videos,
            "audio": models.Audios,
            "image": models.Images,
        }
        get_main = (
            db.query(tableName[content_type])
            .filter(tableName[content_type].user_id == user_id)
            .filter(tableName[content_type].id == content_id)
            .first()
        )
        user_data = db.query(models.Users).filter(models.Users.id == user_id).first()
        if user_data.verified == False:
            return {"detail": "Failed", "data": "User not verified"}
        if get_main is None:
            return {"detail": "Failed", "data": "Unable to fetch content"}
        result_presigned = add_presigned_single(get_main.link, CLOUDFLARE_CONTENT, rd)
        return {"detail": "Success", "data": result_presigned}
    except Exception as e:
        return {"detail": "Failed", "data": "Unable to fetch content"}


@router.get("/download_content", status_code=status.HTTP_200_OK)
async def download_content(
    content_id: int,
    content_type: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
    rd: redis.Redis = Depends(get_redis),
):
    if throttler.consume(identifier="user_id") == False:
        raise HTTPException(status_code=429, detail="Too Many Requests")
    result = download_content_task(
        current_user.user_id, content_id, content_type, db, rd
    )
    if result["detail"] == "Failed":
        raise HTTPException(status_code=400, detail="Unable to fetch content")
    return result


def download_complete_task(
    user_id: int, content_id: int, content_type: str, db: Session, rd: redis.Redis
):
    try:
        tableName = {
            "video": models.Videos,
            "audio": models.Audios,
            "image": models.Images,
        }
        user_dashboard = (
            db.query(models.Dashboard)
            .filter(models.Dashboard.user_id == user_id)
            .first()
        )
        get_main = (
            db.query(tableName[content_type])
            .filter(tableName[content_type].user_id == user_id)
            .filter(tableName[content_type].id == content_id)
            .first()
        )
        if user_dashboard is None:
            return {"detail": "Failed", "data": "Unable to fetch content"}
        obj_data = get_object_data(get_main.link, CLOUDFLARE_CONTENT, rd)
        if obj_data is None:
            return {"detail": "Failed", "data": "Unable to fetch content"}
        print(obj_data)
        size = obj_data["HTTPHeaders"]["content-length"]
        user_dashboard.downloads += int(size)
        db.commit()
        return {"detail": "Success", "data": "Download complete"}
    except Exception as e:
        return {"detail": "Failed", "data": "Unable to fetch content"}


@router.get("/download_complete", status_code=status.HTTP_200_OK)
async def download_complete(
    content_id: int,
    content_type: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
    rd: redis.Redis = Depends(get_redis),
):
    if throttler.consume(identifier="user_id") == False:
        raise HTTPException(status_code=429, detail="Too Many Requests")
    result = download_complete_task(
        current_user.user_id, content_id, content_type, db, rd
    )
    if result["detail"] == "Failed":
        raise HTTPException(status_code=400, detail="Unable to fetch content")
    return result


def isAlpnanumeric(string):
    alphanumeric_pattern = r"^[a-zA-Z0-9._ ]+$"
    return bool(re.match(alphanumeric_pattern, string))


def rename_content_celery(
    content_id: int, content_type: str, newtitle: str, user_id: int, db: Session
):
    try:
        if content_type == "video":
            model_type = models.Videos
        elif content_type == "audio":
            model_type = models.Audios
        elif content_type == "image":
            model_type = models.Images
        else:
            return {"detail": "Failed", "data": "Invalid type"}
        main_file = (
            db.query(model_type)
            .filter(model_type.id == content_id)
            .filter(model_type.user_id == user_id)
            .first()
        )
        if isAlpnanumeric(newtitle) == False:
            return {"detail": "Failed", "data": "Invalid title"}
        if main_file:
            main_file.title = newtitle
            db.commit()
            return {"detail": "Success", "data": "Project renamed"}
        else:
            return {"detail": "Failed", "data": "Project not found"}
    except Exception as e:
        return {"detail": "Failed", "data": str(e)}


@router.put("/rename-content/{id}/{content_type}/{newtitle}")
async def rename_project(
    id: int,
    content_type: str,
    newtitle: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    if throttler.consume(identifier="user_id") == False:
        raise HTTPException(status_code=429, detail="Too Many Requests")
    try:
        result = rename_content_celery(
            id, content_type, newtitle, current_user.user_id, db
        )
        if result["detail"] == "Success":
            return {"detail": "Success", "data": "Content renamed"}
        else:
            raise HTTPException(status_code=400, detail=result["data"])
    except:
        raise HTTPException(status_code=400, detail="Failed to rename content")
