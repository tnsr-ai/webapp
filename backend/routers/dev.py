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
from celeryworker import celeryapp
from utils import throttler
from utils import ENV


def is_test_mode():
    return ENV == "development"


router = APIRouter(
    prefix="/dev", tags=["dev"], responses={404: {"description": "Not found"}}
)

models.Base.metadata.create_all(bind=engine)


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


@router.get("/delete-user")
async def delete_user(
    email: str, db: Session = Depends(get_db), test_mode: bool = Depends(is_test_mode)
):
    if test_mode:
        user = db.query(models.Users).filter(models.Users.email == email).first()
        if not user:
            raise HTTPException(status_code=200, detail="User not found")
        user_id = user.id
        db.query(models.Balance).filter(models.Balance.user_id == user_id).delete()
        db.query(models.Dashboard).filter(models.Dashboard.user_id == user_id).delete()
        db.query(models.UserSetting).filter(
            models.UserSetting.user_id == user_id
        ).delete()
        db.query(models.Users).filter(models.Users.id == user_id).delete()
        db.commit()
        return {"message": "User deleted"}
    else:
        raise HTTPException(status_code=403, detail="Not authorized")


@router.get("/verify-user")
async def verify_user(
    email: str, db: Session = Depends(get_db), test_mode: bool = Depends(is_test_mode)
):
    if test_mode:
        user = db.query(models.Users).filter(models.Users.email == email).first()
        if not user:
            raise HTTPException(status_code=200, detail="User not found")
        user_id = user.id
        user_details = db.query(models.Users).filter(models.Users.id == user_id).first()
        user_details.verified = True
        db.commit()
        return {"message": "User verified"}
    else:
        raise HTTPException(status_code=403, detail="Not authorized")