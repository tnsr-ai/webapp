import sys

sys.path.append("..")

from typing import Optional
from fastapi import Depends, HTTPException, APIRouter
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from script_utils.util import *
from dotenv import load_dotenv
from typing import Optional, Annotated
import time
import json
import hruid
import hashlib
from celeryworker import celeryapp
from cryptography.fernet import Fernet
from routers.auth import authenticate_user, get_current_user, TokenData
from fastapi_limiter.depends import RateLimiter
from utils import LOKI_URL, LOKI_USERNAME, LOKI_PASSWORD, CRYPTO_TOKEN

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


db_dependency = Annotated[Session, Depends(get_db)]


class RegisterJobModel(BaseModel):
    job_type: str
    config_json: dict


@celeryapp.task
def register_job_celery(job_details: dict, user_id: int) -> None:
    try:
        db = SessionLocal()
        generator = hruid.Generator()
        phrase = generator.random()
        user_details = db.query(models.Users).filter(models.Users.id == user_id).first()
        create_job_model = models.Jobs(
            user_id=user_id,
            job_name=phrase,
            job_type=job_details["job_type"],
            job_status="Booting Up",
            job_tier=user_details.user_tier,
            created_at=int(time.time()),
            job_key=True,
            config_json=json.dumps(job_details["config_json"]),
            job_process="started",
            key=hashlib.md5(generator.random().encode()).hexdigest(),
        )
        db.add(create_job_model)
        db.commit()
        db.refresh(create_job_model)
        return {
            "detail": "Success",
            "data": "Job registered successfully",
            "job_id": create_job_model.job_id,
        }
    except Exception as e:
        return {"detail": "Failed", "data": "Unable to update settings"}


@router.post("/register_job", dependencies=[Depends(RateLimiter(times=5, seconds=60))])
async def register_job(
    job_dict: RegisterJobModel,
    db: db_dependency,
    current_user: TokenData = Depends(get_current_user),
):
    try:
        result = register_job_celery.delay(job_dict.dict(), current_user.user_id)
        result = result.get()
        if result["detail"] == "Failed":
            raise HTTPException(status_code=400, detail="Unable to register job")
        # To do: Add celery task to run the job
        return {
            "detail": "Success",
            "data": "Job registered successfully",
            "job_id": result["job_id"],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail="Unable to register job")


@celeryapp.task
def fetch_jobs_celery(job_id: int, key: str):
    try:
        db = SessionLocal()
        jobs = db.query(models.Jobs).filter(models.Jobs.job_id == job_id).first()
        if jobs is None:
            raise HTTPException(status_code=400, detail="Unable to fetch jobs")
        if jobs.key != key or jobs.job_key == False:
            raise HTTPException(status_code=400, detail="Unable to fetch jobs")
        result = {}
        for column in jobs.__table__.columns:
            result[column.name] = str(getattr(jobs, column.name))
        creds_json = {
            "LOKI_URL": LOKI_URL,
            "LOKI_USERNAME": LOKI_USERNAME,
            "LOKI_PASSWORD": LOKI_PASSWORD,
        }
        creds_text = json.dumps(creds_json)
        fernet = Fernet(CRYPTO_TOKEN.encode())
        creds_encrypted = fernet.encrypt(creds_text.encode())
        result["creds"] = creds_encrypted.decode()
        return {"detail": "Success", "data": result}
    except Exception as e:
        return {"detail": "Failed", "data": str(e)}


@router.get("/fetch_jobs")
async def fetch_jobs(job_id: int, key: str, db: db_dependency):
    try:
        result = fetch_jobs_celery.delay(job_id, key)
        result = result.get()
        if result["detail"] == "Failed":
            raise HTTPException(status_code=400, detail="Unable to fetch jobs")
        return {"detail": "Success", "data": result["data"]}
    except Exception as e:
        raise HTTPException(status_code=400, detail="Unable to fetch jobs")


@router.get("/fetch_routes", dependencies=[Depends(RateLimiter(times=60, seconds=60))])
async def fetch_routes():
    try:
        ROUTES = {
            "getjob": "/jobs/fetch_jobs",
            "registerjob": "/jobs/register_job",
            "presignedurl": "/upload/generate_presigned_post",
            "indexfile": "/upload/indexfile",
            "updatejob": "/jobs/update_job_status",
        }
        return {"detail": "Success", "data": ROUTES}
    except Exception as e:
        raise HTTPException(status_code=400, detail="Unable to fetch routes")


@celeryapp.task
def update_job_status_celery(job_id: int, job_status: str, job_process: str, key: str):
    try:
        db = SessionLocal()
        jobs = db.query(models.Jobs).filter(models.Jobs.job_id == job_id).first()
        if jobs.key != key or jobs.job_key == False:
            raise HTTPException(status_code=400, detail="Unable to update job status")
        jobs.job_status = job_status
        jobs.job_process = job_process
        db.commit()
        return {"detail": "Success", "data": "Job status updated successfully"}
    except Exception as e:
        return {"detail": "Failed", "data": str(e)}


@router.post(
    "/update_job_status", dependencies=[Depends(RateLimiter(times=60, seconds=60))]
)
async def update_job_status(
    job_id: int, job_status: str, job_process: str, key: str, db: db_dependency
):
    try:
        result = update_job_status_celery.delay(job_id, job_status, job_process, key)
        result = result.get()
        if result["detail"] == "Failed":
            raise HTTPException(status_code=400, detail="Unable to update job status")
        return {"detail": "Success", "data": "Job status updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail="Unable to update job status")


@celeryapp.task
async def send_notification_celery(user_id: int, job_id: int):
    try:
        pass
        # To do: Add celery task to send notification
    except Exception as e:
        return {"detail": "Failed", "data": str(e)}


@router.post(
    "/send_notification", dependencies=[Depends(RateLimiter(times=30, seconds=60))]
)
async def send_notification(user_id: int, job_id: int, db: db_dependency):
    try:
        result = send_notification_celery.delay(user_id, job_id)
        result = result.get()
        if result["detail"] == "Failed":
            raise HTTPException(status_code=400, detail="Unable to send notification")
        return {"detail": "Success", "data": "Notification sent successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail="Unable to send notification")
