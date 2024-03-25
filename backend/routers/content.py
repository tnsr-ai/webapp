import sys

from script_utils.util import niceBytes

sys.path.append("..")

from typing import Optional
from fastapi import Depends, HTTPException, APIRouter, status
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from pydantic import BaseModel, Field
import boto3, botocore
import redis
from celeryworker import celeryapp
from routers.auth import get_current_user, TokenData
import json
import re
from fastapi_limiter.depends import RateLimiter
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
from utils import remove_key, logger, presigned_get, delete_r2_file
from script_utils.util import bytes_to_mb


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


def allTags(id: bool = False):
    rd = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
    if id == False:
        rd_key = "all_tags"
    else:
        rd_key = "all_tags_id"
    if rd.exists(rd_key):
        return json.loads(rd.get(rd_key).decode("utf-8"))
    db = SessionLocal()
    tags = db.query(models.Tags).all()
    db.close()
    all_tags = {}
    if id == False:
        for tag in tags:
            all_tags[tag.tag] = {
                "id": int(tag.id),
                "readable": tag.readable,
            }
        rd.set(rd_key, json.dumps(all_tags))
        return all_tags
    else:
        for tag in tags:
            all_tags[int(tag.id)] = {
                "tag": tag.tag,
                "readable": tag.readable,
            }
        rd.set(rd_key, json.dumps(all_tags))
        return all_tags


def add_presigned(data, key, result_key, bucket, rd):
    for x in data:
        x[result_key] = presigned_get(x[key], bucket, rd)
    return data


def add_presigned_single(file_key, bucket, rd):
    try:
        if rd is not None and rd.exists(file_key):
            return rd.get(file_key).decode("utf-8")
        r2_client = boto3.client(
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
        response = r2_client.generate_presigned_url(
            ClientMethod="get_object",
            Params={
                "Bucket": bucket,
                "Key": file_key,
            },
            ExpiresIn=CONTENT_EXPIRE,
        )
        if rd is not None:
            rd.set(file_key, response)
            rd.expire(file_key, CONTENT_EXPIRE - 43200)
        return response
    except Exception as e:
        print(str(e))
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
            endpoint_url=CLOUDFLARE_ACCOUNT_ENDPOINT,
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
        if x["size"] is not None:
            x["size"] = niceBytes(x["size"])
    return data


def get_content_table(user_id, table_name, limit, offset, db):
    try:
        get_table = (
            db.query(models.Content)
            .filter(models.Content.user_id == user_id)
            .filter(models.Content.id_related == None)
            .filter(models.Content.status == "completed")
            .filter(models.Content.content_type == table_name)
            .order_by(models.Content.created_at.desc())
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
            db.query(models.Content)
            .filter(models.Content.user_id == user_id)
            .filter(models.Content.id_related == None)
            .filter(models.Content.status == "completed")
            .count()
        )
        return {"detail": "Success", "data": [all_result, get_counts]}
    except Exception as e:
        return {"detail": "Failed", "data": "Unable to fetch content"}


@router.get(
    "/get_content",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(times=60, seconds=60))],
)
async def get_content(
    limit: int,
    offset: int,
    content_type: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
    rd: redis.Redis = Depends(get_redis),
):
    try:
        if limit > 12:
            logger.error("Limit cannot be more than 12")
            raise HTTPException(status_code=400, detail="Limit cannot be more than 10")
        result_ = get_content_table(
            current_user.user_id, content_type, limit, offset, db
        )
        if result_["detail"] == "Failed":
            logger.error("Unable to fetch content")
            raise HTTPException(status_code=400, detail="Unable to fetch content")
        result_ = result_["data"]
        result = add_presigned(
            result_[0], "thumbnail", "thumbnail_link", CLOUDFLARE_METADATA, rd
        )
        result = filter_data(result)
        result = {"data": result, "detail": "Success", "total": result_[1]}
        logger.info("Content fetched successfully")
        return result
    except Exception as e:
        logger.error("Something went wrong - " + str(e))
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
        get_counts = (
            db.query(models.Content)
            .filter(models.Content.user_id == user_id)
            .filter(models.Content.id_related == content_id)
            .filter(models.Content.content_type == content_type)
            .filter(
                or_(
                    models.Content.status == "processing",
                    models.Content.status == "completed",
                )
            )
            .count()
            + 1
        )
        get_main = (
            db.query(models.Content)
            .filter(models.Content.user_id == user_id)
            .filter(models.Content.id == content_id)
            .filter(models.Content.content_type == content_type)
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
                db.query(models.Content)
                .filter(models.Content.user_id == user_id)
                .filter(models.Content.id == content_id)
                .filter(models.Content.content_type == content_type)
                .first()
            )
            if get_main is None:
                return {"detail": "Failed", "data": "Unable to fetch content"}
            get_related = (
                db.query(models.Content)
                .filter(models.Content.user_id == user_id)
                .filter(models.Content.id_related == content_id)
                .filter(
                    or_(
                        models.Content.status == "processing",
                        models.Content.status == "completed",
                    )
                )
                .order_by(models.Content.created_at.desc())
                .limit(limit - 1)
                .offset(offset)
                .all()
            )
            result = [get_main.__dict__]
            for x in get_related:
                result.append(x.__dict__)
            remove_key(result, "_sa_instance_state")
            all_tags = allTags(id=True)
            for x in result:
                tags_query = (
                    db.query(models.ContentTags)
                    .filter(models.ContentTags.content_id == int(x["id"]))
                    .all()
                )
                all_content_tags = []
                for y in tags_query:
                    all_content_tags.append(y.tag_id)
                x["tags"] = []
                for tag in all_content_tags:
                    x["tags"].append((all_tags[str(tag)]["readable"]))
                x["tags"] = ",".join(x["tags"])
            return {
                "detail": "Success",
                "data": result,
                "total": get_counts,
                "title": main_title,
            }
        else:
            get_related = (
                db.query(models.Content)
                .filter(models.Content.user_id == user_id)
                .filter(models.Content.id_related == content_id)
                .filter(models.Content.content_type == content_type)
                .filter(
                    or_(
                        models.Content.status == "processing",
                        models.Content.status == "completed",
                    )
                )
                .order_by(models.Content.created_at.desc())
                .limit(limit)
                .offset(offset - 1)
                .all()
            )
            result = []
            for x in get_related:
                result.append(x.__dict__)
            remove_key(result, "_sa_instance_state")
            all_tags = allTags(id=True)
            for x in result:
                tags_query = (
                    db.query(models.ContentTags)
                    .filter(models.ContentTags.content_id == int(x["id"]))
                    .all()
                )
                all_content_tags = []
                for y in tags_query:
                    all_content_tags.append(y.tag_id)
                x["tags"] = []
                for tag in all_content_tags:
                    x["tags"].append((all_tags[str(tag)]["readable"]))
                x["tags"] = ",".join(x["tags"])
            return {
                "detail": "Success",
                "data": result,
                "total": get_counts,
                "title": main_title,
            }
    except Exception as e:
        print(str(e))
        return {"detail": "Failed", "data": "Unable to fetch content"}


@router.get(
    "/get_content_list",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(times=60, seconds=60))],
)
async def get_content_list(
    limit: int,
    offset: int,
    content_id: int,
    content_type: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
    rd: redis.Redis = Depends(get_redis),
):
    if limit > 5:
        logger.error("Limit cannot be more than 5")
        raise HTTPException(status_code=400, detail="Limit cannot be more than 5")
    try:
        result = get_content_list_celery(
            db, content_id, content_type, current_user.user_id, limit, offset
        )
        if result["detail"] == "Failed":
            logger.error("Unable to fetch content - " + str(result["data"]))
            raise HTTPException(status_code=400, detail="Unable to fetch content")
        if len(result["data"]) == 0:
            logger.error("No more content")
            raise HTTPException(status_code=400, detail="No more content")
        result["data"] = add_presigned(
            result["data"], "thumbnail", "thumbnail_link", CLOUDFLARE_METADATA, rd
        )
        result["data"] = add_presigned(
            result["data"], "link", "content_link", CLOUDFLARE_CONTENT, rd
        )
        result["data"] = filter_data(result["data"])
        logger.info("Content fetched successfully")
        return result
    except Exception as e:
        logger.error("Something went wrong - " + str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Something went wrong"
        )


def download_content_task(
    user_id: int, content_id: int, content_type: str, db: Session, rd: redis.Redis
):
    try:
        get_main = (
            db.query(models.Content)
            .filter(models.Content.user_id == user_id)
            .filter(models.Content.id == content_id)
            .filter(models.Content.content_type == content_type)
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


@router.get(
    "/download_content",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(times=30, seconds=60))],
)
async def download_content(
    content_id: int,
    content_type: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
    rd: redis.Redis = Depends(get_redis),
):
    result = download_content_task(
        current_user.user_id, content_id, content_type, db, rd
    )
    if result["detail"] == "Failed":
        logger.error("Unable to fetch content - " + str(result["data"]))
        raise HTTPException(status_code=400, detail="Unable to fetch content")
    logger.info("Content fetched successfully")
    return result


def download_complete_task(
    user_id: int, content_id: int, content_type: str, db: Session, rd: redis.Redis
):
    try:
        user_dashboard = (
            db.query(models.Dashboard)
            .filter(models.Dashboard.user_id == user_id)
            .first()
        )
        get_main = (
            db.query(models.Content)
            .filter(models.Content.user_id == user_id)
            .filter(models.Content.id == content_id)
            .filter(models.Content.content_type == content_type)
            .first()
        )
        if user_dashboard is None:
            return {"detail": "Failed", "data": "Unable to fetch content"}
        obj_data = get_object_data(get_main.link, CLOUDFLARE_CONTENT, rd)
        if obj_data is None:
            return {"detail": "Failed", "data": "Unable to fetch content"}
        size = obj_data["HTTPHeaders"]["content-length"]
        user_dashboard.downloads += int(size)
        db.commit()
        return {"detail": "Success", "data": "Download complete"}
    except Exception as e:
        return {"detail": "Failed", "data": "Unable to fetch content"}


@router.get(
    "/download_complete",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(times=60, seconds=60))],
)
async def download_complete(
    content_id: int,
    content_type: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
    rd: redis.Redis = Depends(get_redis),
):
    result = download_complete_task(
        current_user.user_id, content_id, content_type, db, rd
    )
    if result["detail"] == "Failed":
        logger.error("Unable to fetch content - " + str(result["data"]))
        raise HTTPException(status_code=400, detail="Unable to fetch content")
    logger.info("Download completed successfully")
    return result


def isAlpnanumeric(string):
    alphanumeric_pattern = r"^[a-zA-Z0-9._ ]+$"
    return bool(re.match(alphanumeric_pattern, string))


def rename_content_celery(
    content_id: int, content_type: str, newtitle: str, user_id: int, db: Session
):
    try:
        if content_type not in ["video", "audio", "image"]:
            return {"detail": "Failed", "data": "Invalid type"}
        main_file = (
            db.query(models.Content)
            .filter(models.Content.id == content_id)
            .filter(models.Content.user_id == user_id)
            .filter(models.Content.content_type == content_type)
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


@router.put(
    "/rename-content/{id}/{content_type}/{newtitle}",
    dependencies=[Depends(RateLimiter(times=30, seconds=60))],
)
async def rename_project(
    id: int,
    content_type: str,
    newtitle: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    try:
        if len(newtitle) > 30 or len(newtitle) < 3:
            raise HTTPException(status_code=400, detatil="Invalid Title")
        result = rename_content_celery(
            id, content_type, newtitle, current_user.user_id, db
        )
        if result["detail"] == "Success":
            logger.info("Content renamed successfully")
            return {"detail": "Success", "data": "Content renamed"}
        else:
            logger.error("Failed to rename content - " + str(result["data"]))
            raise HTTPException(status_code=400, detail=result["data"])
    except:
        logger.error("Failed to rename content")
        raise HTTPException(status_code=400, detail="Failed to rename content")




def delete_content_task(
    content_id: int, content_type: str, user_id: int, db: Session
):
    try:
        if content_type not in ["video", "audio", "image"]:
            return {"detail": "Failed", "data": "Invalid type"}
        main_file = (
            db.query(models.Content)
            .filter(models.Content.id == content_id)
            .filter(models.Content.user_id == user_id)
            .filter(models.Content.content_type == content_type)
            .filter(models.Content.status == "completed")
            .first()
        )
        if main_file:
            dashboard_user = (
                db.query(models.Dashboard)
                .filter(models.Dashboard.user_id == user_id)
                .first()
            )
            attached_content = (
                db.query(models.Content)
                .filter(models.Content.id_related == content_id)
                .filter(models.Content.user_id == user_id)
                .filter(models.Content.content_type == content_type)
                .all()
            )
            attached_content.append(main_file)
            for all_content in attached_content:
                file_size = "".join([x for x in all_content.size if x.isdigit() or x == "."])
                if content_type == "video":
                    dashboard_user.video_processed = int(dashboard_user.video_processed) - 1
                    storageJSON = json.loads(dashboard_user.storage_json)
                    storageJSON["video"] = float(storageJSON["video"]) - bytes_to_mb(
                        float(file_size)
                    )
                    dashboard_user.storage_json = json.dumps(storageJSON)
                elif content_type == "audio":
                    dashboard_user.audio_processed = int(dashboard_user.audio_processed) - 1
                    storageJSON = json.loads(dashboard_user.storage_json)
                    storageJSON["audio"] = float(storageJSON["audio"]) - bytes_to_mb(
                        float(file_size)
                    )
                    dashboard_user.storage_json = json.dumps(storageJSON)
                elif content_type == "image":
                    dashboard_user.image_processed = int(dashboard_user.image_processed) - 1
                    storageJSON = json.loads(dashboard_user.storage_json)
                    storageJSON["image"] = float(storageJSON["image"]) - bytes_to_mb(
                        float(file_size)
                    )
                    dashboard_user.storage_json = json.dumps(storageJSON)
                dashboard_user.storage_used = float(dashboard_user.storage_used) - float(
                    file_size
                )
                if all_content.status == "processing":
                    return {"detail": "Failed", "data": "Running Job Found"}
                related_tags = (
                    db.query(models.ContentTags)
                    .filter(models.ContentTags.content_id == all_content.id)
                    .all()
                )
                for tag in related_tags:
                    db.delete(tag)
                if all_content.status == "completed":
                    delete_r2_file.delay(all_content.link, CLOUDFLARE_CONTENT)
                    delete_r2_file.delay(all_content.thumbnail, CLOUDFLARE_METADATA)
                db.delete(all_content)
            # main_tag = (
            #     db.query(models.ContentTags)
            #     .filter(models.ContentTags.content_id == main_file.id)
            #     .all()
            # )
            # for tag in main_tag:
            #     db.delete(tag)
            # db.delete(main_file)
            db.commit()
            return {"detail": "Success", "data": "Project Deleted"}
        else:
            return {"detail": "Failed", "data": "Project not found"}
    except Exception as e:
        return {"detail": "Failed", "data": str(e)}


@router.delete(
    "/delete-content/{id}/{content_type}",
    dependencies=[Depends(RateLimiter(times=30, seconds=60))],
)
async def delete_content(
    id: int,
    content_type: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    try:
        result = delete_content_task(
            id, content_type,  current_user.user_id, db
        )
        if result["detail"] == "Success":
            logger.info("Content renamed successfully")
            return {"detail": "Success", "data": "Project deleted"}
        else:
            logger.error("Failed to delete project - " + str(result["data"]))
            raise HTTPException(status_code=400, detail=result["data"])
    except:
        logger.error("Failed to delete project")
        raise HTTPException(status_code=400, detail="Failed to delete project")
