import sys

sys.path.append("..")

from typing import Annotated
from fastapi import Depends, HTTPException, APIRouter, Response
import models
import time
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from starlette import status
from routers.auth import TokenData, get_current_user
from utils import sql_dict, logger
from utils import STORAGE_LIMITS
from fastapi_limiter.depends import RateLimiter
from script_utils.util import *
from humanfriendly import format_timespan


router = APIRouter(
    prefix="/dashboard", tags=["dashboard"], responses={401: {"user": "Not authorized"}}
)


models.Base.metadata.create_all(bind=engine)


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


def create_balance(db, user_id: int):
    balance = models.Balance(
        user_id=user_id, balance=0.0, lifetime_usage=0.0, created_at=int(time.time())
    )
    db.add(balance)
    db.commit()
    db.refresh(balance)
    return balance


def create_dashboard(db, user_id: int, storage_limit: int):
    dashboard = models.Dashboard(
        user_id=user_id,
        video_processed=0,
        audio_processed=0,
        image_processed=0,
        downloads=0,
        uploads=0,
        storage_used=0,
        storage_limit=storage_limit,
        gpu_usage=0,
        storage_json="""{'video':0, 'audio':0, 'image':0}""",
        created_at=int(time.time()),
    )
    db.add(dashboard)
    db.commit()
    db.refresh(dashboard)
    return dashboard


def dashboard_task(id: int, db: Session):
    try:
        user = db.query(models.Dashboard).filter(models.Dashboard.user_id == id).first()
        user_details = db.query(models.Users).filter(models.Users.id == id).first()
        user_balance = (
            db.query(models.Balance).filter(models.Balance.user_id == id).first()
        )

        if user_balance is None:
            user_balance = create_balance(db, id)

        if user is None:
            storage_limit = STORAGE_LIMITS.get(
                user_details.user_tier, STORAGE_LIMITS["free"]
            )
            user = create_dashboard(db, id, storage_limit)

        data = sql_dict(user)
        data["name"] = user_details.first_name
        data["balance"] = float(user_balance.balance)
        return {
            "detail": "Success",
            "data": data,
            "verified": user_details.verified,
        }
    except Exception as e:
        return {"detail": "Failed", "data": str(e)}


@router.get(
    "/get_stats",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(times=60, seconds=60))],
)
async def get_stats(
    current_user: TokenData = Depends(get_current_user), db: Session = Depends(get_db)
):
    result = dashboard_task(current_user.user_id, db)
    if result["detail"] == "Success":
        logger.info(f"Dashboard stats for {current_user.user_id}")
        result["data"]["downloads"] = nice_unit(niceBytes(result["data"]["downloads"]))
        result["data"]["uploads"] = nice_unit(niceBytes(result["data"]["uploads"]))
        result["data"]["gpu_usage"] = format_timespan(result["data"]["gpu_usage"], max_units=1)
        result["data"][
            "storage"
        ] = f"{nice_unit(niceBytes(result['data']['storage_used']))} / {nice_unit(niceBytes(result['data']['storage_limit']))}"
        logger.info(f"Dashboard stats for {current_user.user_id} success")
        return result
    else:
        logger.error(f"Dashboard stats for {current_user.user_id} failed")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=result["data"]
        )
