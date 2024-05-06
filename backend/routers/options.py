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
from utils import r2_resource, r2_client, logger
from routers.auth import get_current_user, TokenData
import models
from script_utils.util import *
from dotenv import load_dotenv
from utils import TNSR_DOMAIN, CLOUDFLARE_CONTENT, CLOUDFLARE_METADATA, USER_TIER
from celeryworker import celeryapp
from fastapi_limiter.depends import RateLimiter

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


def delete_project_celery(content_id: int, content_type: str, user_id: int, db: Session):
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
            for file in attached_content:
                if str(file.status) == "processing":
                    return {"detail": "Failed", "data": "Please cancel the running job first"}
            for all_content in attached_content:
                job_data = (
                    db.query(models.Jobs)
                    .filter(models.Jobs.content_id == all_content.id)
                    .first()
                )
                try:
                    file_size = "".join([x for x in all_content.size if x.isdigit() or x == "."])
                except:
                    file_size = 0
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
                related_tags = (
                    db.query(models.ContentTags)
                    .filter(models.ContentTags.content_id == all_content.id)
                    .all()
                )
                for tag in related_tags:
                    db.delete(tag)
                if str(all_content.status) == "completed":
                    delete_r2_file.delay(all_content.link, CLOUDFLARE_CONTENT)
                    delete_r2_file.delay(all_content.thumbnail, CLOUDFLARE_METADATA)
                if job_data is not None:
                    db.delete(job_data)
                db.delete(all_content)
            db.commit()
            return {"detail": "Success", "data": "Project Deleted"}
        else:
            return {"detail": "Failed", "data": "Project not found"}
    except Exception as e:
        logger.error(f"Failed to delete project {id} - {str(e)}")
        return {"detail": "Failed", "data": "Failed to delete project"}


@router.delete(
    "/delete-project/{id}/{content_type}",
    dependencies=[Depends(RateLimiter(times=30, seconds=60))],
)
async def delete_project(
    id: int,
    content_type: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    result = delete_project_celery(id, content_type, current_user.user_id, db)
    if result["detail"] == "Success":
        logger.info(f"Project deleted {id}")
        return {"detail": "Success", "data": "Project deleted"}
    else:
        logger.error(f"Failed to delete project {id}")
        raise HTTPException(status_code=400, detail=result["data"])



def rename_project_celery(
    id: int, content_type: str, newtitle: str, user_id: int, db: Session
):
    try:
        if content_type not in ["video", "audio", "image"]:
            return {"detail": "Failed", "data": "Invalid type"}
        main_file = (
            db.query(models.Content)
            .filter(models.Content.id == id)
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
    "/rename-project/{id}/{content_type}/{newtitle}",
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
        result = rename_project_celery(
            id, content_type, newtitle, current_user.user_id, db
        )
        if result["detail"] == "Success":
            logger.info(f"Project renamed {id}")
            return {"detail": "Success", "data": "Project renamed"}
        else:
            logger.error(f"Failed to rename project {id}")
            raise HTTPException(status_code=400, detail=result["data"])
    except:
        logger.error(f"Failed to rename project {id}")
        raise HTTPException(status_code=400, detail="Failed to rename project")


@celeryapp.task(name="routers.options.resend_email_task", acks_late=True)
def resend_email_task(user_id: int):
    with Session(engine) as db:
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
        verification_link = f"{TNSR_DOMAIN}/verifyemail/?user_id={user_id}&email_token={email_token['token']}"
        email_status = registration_email(
            user_data.first_name, verification_link, user_data.email
        )
        if email_status != True:
            return {"detail": "Failed", "data": "Failed to send email"}
        return {"detail": "Success", "data": "Email sent successfully"}


@router.post(
    "/resend-email",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimiter(times=10, seconds=60))],
)
async def resend_email(
    response: Response,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = (
        db.query(models.Users).filter(models.Users.id == current_user.user_id).first()
    )
    if not user:
        logger.error(f"User not found {current_user.user_id}")
        raise HTTPException(status_code=400, detail="User not found")
    if user.verified == True:
        logger.error(f"Email already verified {current_user.user_id}")
        raise HTTPException(status_code=400, detail="Email already verified")
    resend_email_task.delay(current_user.user_id)
    logger.info(f"Resend email {current_user.user_id}")
    return {"detail": "Success", "data": "Email sent successfully"}

@router.get(
    "/user_tier",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(times=60, seconds=60))]
)
async def user_tier(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = (
        db.query(models.Users).filter(models.Users.id == current_user.user_id).first()
    )
    if not user:
        logger.error(f"User not found {current_user.user_id}")
        raise HTTPException(status_code=400, detail="User not found")
    user_tier = str(user.user_tier)
    return USER_TIER[user_tier]

