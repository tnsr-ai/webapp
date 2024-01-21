import sys

sys.path.append("..")

from typing import Optional
from fastapi import Depends, HTTPException, APIRouter, status
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
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
from utils import getTags
from routers.content import add_presigned_single

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
        table_type = {
            "video": models.Videos,
            "audio": models.Audios,
            "image": models.Images,
        }
        table = table_type[config["job_type"]]
        content_detail = (
            db.query(table)
            .filter(table.id == config["config_json"]["job_data"]["content_id"])
            .first()
        )
        if content_detail is None:
            raise HTTPException(status_code=400, detail="Content not found")
        if content_detail.user_id != user_id:
            raise HTTPException(status_code=400, detail="Content not found")
        tags = [
            getTags(x, config["job_type"])
            for x in config["config_json"]["job_data"]["filters"].keys()
            if config["config_json"]["job_data"]["filters"][x]["active"] == True
        ]
        create_content_model = table(
            user_id=user_id,
            title=content_detail.title,
            thumbnail=content_detail.thumbnail,
            tags=",".join(tags),
            id_related=content_detail.id,
            created_at=int(time.time()),
            status="pending",
        )
        db.add(create_content_model)
        db.commit()
        db.refresh(create_content_model)
        return create_content_model.id
    except Exception as e:
        raise HTTPException(status_code=400, detail="Unable to create content entry")


@router.post("/register_job", dependencies=[Depends(RateLimiter(times=5, seconds=60))])
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
        return {"detail": "Success", "data": "Job registered successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail="Unable to register job")


def fetch_content_data(content_id: int, table: str, db: Session):
    try:
        table_type = {
            "video": models.Videos,
            "audio": models.Audios,
            "image": models.Images,
        }
        content_detail = (
            db.query(table_type[table])
            .filter(table_type[table].id == content_id)
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
        for job in job_details:
            content_detail = fetch_content_data(
                job["content_id"], job["job_type"], db
            ).__dict__
            content_detail.pop("_sa_instance_state")
            content_detail = {k: v for k, v in content_detail.items() if v is not None}
            content_detail["thumbnail"] = add_presigned_single(
                content_detail["thumbnail"], CLOUDFLARE_METADATA, rd
            )
            if content_detail["status"].value != "pending":
                job_details.remove(job)
                continue
            job["content_detail"] = content_detail
        return {"detail": "Success", "data": job_details}
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
        if limit > 5:
            raise HTTPException(
                status_code=400, detail="Limit cannot be greater than 5"
            )
        job_details = (
            db.query(models.Jobs)
            .filter(models.Jobs.user_id == current_user.user_id)
            .limit(limit)
            .offset(offset)
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
            job["content_detail"] = content_detail
            if content_detail["status"].value != "pending":
                final_data.append(job)
        return {"detail": "Success", "data": final_data}
    except Exception as e:
        raise HTTPException(status_code=400, detail="Unable to fetch jobs")
