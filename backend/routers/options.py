import json
import secrets
import sys

sys.path.append("..")
import time
from typing import Annotated
from fastapi import Depends, HTTPException, APIRouter, Response, status, Request
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session
import re
from utils import *
from routers.auth import get_current_user, TokenData
import models
from script_utils.util import *
from dotenv import load_dotenv
from utils import DOMAIN
from utils import throttler

load_dotenv()


router = APIRouter(
    prefix="/options", tags=["options"], responses={404: {"description": "Not allowed"}}
)

models.Base.metadata.create_all(bind=engine)


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


def isAlpnanumeric(string):
    alphanumeric_pattern = r"^[a-zA-Z0-9._ ]+$"
    return bool(re.match(alphanumeric_pattern, string))


db_dependency = Annotated[Session, Depends(get_db)]


def delete_project_celery(id: int, content_type: str, user_id: int):
    try:
        db = SessionLocal()
        if content_type == "video":
            model_type = models.Videos
        elif content_type == "audio":
            model_type = models.Audios
        elif content_type == "image":
            model_type = models.Images
        else:
            return {"detail": "Failed", "data": "Invalid type"}
        dashboard_user = (
            db.query(models.Dashboard)
            .filter(models.Dashboard.user_id == user_id)
            .first()
        )
        main_file = (
            db.query(model_type)
            .filter(model_type.id == id)
            .filter(model_type.user_id == user_id)
            .first()
        )
        if main_file:
            main_key = f"{OBJECT_BUCKET}/" + main_file.link
            main_bucket = r2_resource.Bucket(OBJECT_BUCKET)
            main_bucket.Object(main_key).delete()
            thumbnail_key = f"{THUMBNAIL_BUCKET}/" + main_file.thumbnail
            thumbnail_bucket = r2_resource.Bucket(THUMBNAIL_BUCKET)
            thumbnail_bucket.Object(thumbnail_key).delete()
            db.delete(main_file)
            file_size = "".join([x for x in main_file.size if x.isdigit() or x == "."])
            if content_type == "video":
                dashboard_user.video_processed = int(dashboard_user.video_processed) - 1
            elif content_type == "audio":
                dashboard_user.audio_processed = int(dashboard_user.audio_processed) - 1
            elif content_type == "image":
                dashboard_user.image_processed = int(dashboard_user.image_processed) - 1
            dashboard_user.storage_used = float(dashboard_user.storage_used) - float(
                file_size
            )
            db.commit()
        related_file = (
            db.query(model_type)
            .filter(model_type.id_related == id)
            .filter(model_type.user_id == user_id)
            .all()
        )
        if related_file:
            for file in related_file:
                main_key = f"{OBJECT_BUCKET}/" + file.link
                main_bucket = r2_resource.Bucket(OBJECT_BUCKET)
                main_bucket.Object(main_key).delete()
                thumbnail_key = f"{THUMBNAIL_BUCKET}/" + file.thumbnail
                thumbnail_bucket = r2_resource.Bucket(THUMBNAIL_BUCKET)
                thumbnail_bucket.Object(thumbnail_key).delete()
                db.delete(file)
                file_size = "".join([x for x in file.size if x.isdigit() or x == "."])
                if content_type == "video":
                    dashboard_user.video_processed = (
                        int(dashboard_user.video_processed) - 1
                    )
                elif content_type == "audio":
                    dashboard_user.audio_processed = (
                        int(dashboard_user.audio_processed) - 1
                    )
                elif content_type == "image":
                    dashboard_user.image_processed = (
                        int(dashboard_user.image_processed) - 1
                    )
                dashboard_user.storage_used = float(
                    dashboard_user.storage_used
                ) - float(file_size)
                db.commit()
        return {"detail": "Success", "data": "Project deleted"}
    except Exception as e:
        return {"detail": "Failed", "data": str(e)}


@router.delete("/delete-project/{id}/{content_type}")
async def delete_project(
    id: int,
    content_type: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    if throttler.consume(identifier="user_id") == False:
        raise HTTPException(status_code=429, detail="Too Many Requests")
    try:
        result = delete_project_celery(id, content_type, current_user.user_id)
        if result["detail"] == "Success":
            return {"detail": "Success", "data": "Project deleted"}
        else:
            raise HTTPException(status_code=400, detail=result["data"])
    except:
        raise HTTPException(status_code=400, detail="Failed to delete project")


def rename_project_celery(id: int, content_type: str, newtitle: str, user_id: int):
    try:
        db = SessionLocal()
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
            .filter(model_type.id == id)
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


@router.put("/rename-project/{id}/{content_type}/{newtitle}")
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
        result = rename_project_celery(id, content_type, newtitle, current_user.user_id)
        if result["detail"] == "Success":
            return {"detail": "Success", "data": "Project renamed"}
        else:
            raise HTTPException(status_code=400, detail=result["data"])
    except:
        raise HTTPException(status_code=400, detail="Failed to rename project")


def resend_email_task(user_id: int):
    db = SessionLocal()
    email_token = {
        "token": secrets.token_urlsafe(32),
        "expires": int(time.time()) + 172800,
    }
    user_data = db.query(models.Users).filter(models.Users.id == user_id).first()
    if not user_data:
        return {"detail": "Failed", "data": "User not found"}
    if user_data.verified == True:
        return {"detail": "Failed", "data": "Email already verified"}
    user_data.email_token = json.dumps(email_token)
    db.commit()
    verification_link = (
        f"{DOMAIN}/verifyemail/?user_id={user_id}&email_token={email_token['token']}"
    )
    email_status = registration_email(
        user_data.first_name, verification_link, user_data.email
    )
    if email_status != True:
        return {"detail": "Failed", "data": "Failed to send email"}
    return {"detail": "Success", "data": "Email sent successfully"}


@router.post("/resend-email", status_code=status.HTTP_201_CREATED)
async def resend_email(
    response: Response,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    if throttler.consume(identifier="user_id") == False:
        raise HTTPException(status_code=429, detail="Too Many Requests")
    result = resend_email_task(current_user.user_id)
    return {"detail": "Success", "data": "Email sent successfully"}
