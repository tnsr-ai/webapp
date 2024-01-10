import base64
import json
import sys

sys.path.append("..")
import time
from typing import Optional, Annotated
from fastapi import Depends, HTTPException, APIRouter, Response, status, Request
import models
import os
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from utils import *
from routers.auth import authenticate_user, get_current_user, TokenData
import models
from script_utils.util import *
from dotenv import load_dotenv

load_dotenv()


router = APIRouter(
    prefix="/settings",
    tags=["settings"],
    responses={404: {"description": "Not allowed"}},
)

models.Base.metadata.create_all(bind=engine)


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


class PasswordDict(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str


class NotificationDict(BaseModel):
    newsletter: bool
    email_notification: bool
    discord_webhook: str


def change_password_task(passworddict: dict, user_id: int, db: Session) -> None:
    try:
        user = db.query(models.Users).filter(models.Users.id == user_id).first()
        user = authenticate_user(user.email, passworddict["current_password"], db)
        if user is False:
            return {"detail": "Failed", "data": "Incorrect password"}
        if not user:
            return {"detail": "Failed", "data": "Incorrect password"}
        if passworddict["new_password"] != passworddict["confirm_password"]:
            return {"detail": "Failed", "data": "Password do not match"}
        if passworddict["current_password"] == passworddict["new_password"]:
            return {
                "detail": "Failed",
                "data": "Password cannot be same as old password",
            }
        user = db.query(models.Users).filter(models.Users.email == user.email).first()
        user.hashed_password = get_hashed_password(passworddict["new_password"])
        db.commit()
        return {"detail": "Success", "data": "Password changed successfully"}
    except Exception as e:
        return {"detail": "Failed", "data": "Unable to change password"}


@router.post("/change_password")
async def change_password(
    passworddict: PasswordDict,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        task = change_password_task(passworddict.dict(), int(current_user.user_id), db)
        return task
    except Exception as e:
        return {"detail": "Failed", "data": "Unable to change password"}


def get_settings_task(user_id: int, db: Session) -> None:
    try:
        user = db.query(models.Users).filter(models.Users.id == user_id).first()
        if user is None:
            return {"detail": "Failed", "data": "User not found"}
        details = {}
        details["first_name"] = user.first_name
        details["last_name"] = user.last_name
        details["email"] = user.email
        user_settings = (
            db.query(models.UserSetting)
            .filter(models.UserSetting.user_id == user_id)
            .first()
        )
        if user_settings is None:
            create_user_settings = models.UserSetting(
                user_id=user_id,
                newsletter=True,
                email_notification=True,
                discord_webhook="",
                created_at=int(time.time()),
            )
            db.add(create_user_settings)
            db.commit()
            details["newsletter"] = True
            details["email_notification"] = True
            details["discord_webhook"] = ""
        else:
            details["newsletter"] = user_settings.newsletter
            details["email_notification"] = user_settings.email_notification
            details["discord_webhook"] = user_settings.discord_webhook
        return {"detail": "Success", "data": details, "verified": user.verified}
    except Exception as e:
        return {"detail": "Failed", "data": "Unable to retrieve data"}


@router.get("/get_settings")
async def get_settings(
    db: Session = Depends(get_db), current_user: TokenData = Depends(get_current_user)
):
    try:
        get_details = get_settings_task(current_user.user_id, db)
        return get_details
    except Exception as e:
        return {"detail": "Failed", "data": "Unable to retrieve data"}


def update_settings_task(new_settings: dict, user_id: int, db: Session) -> None:
    try:
        settings = (
            db.query(models.UserSetting)
            .filter(models.UserSetting.user_id == user_id)
            .first()
        )
        if settings is None:
            return {"detail": "Failed", "data": "User not found"}
        settings.newsletter = new_settings["newsletter"]
        settings.email_notification = new_settings["email_notification"]
        settings.discord_webhook = new_settings["discord_webhook"]
        settings.updated_at = int(time.time())
        db.commit()
        return {"detail": "Success", "data": "Settings updated successfully"}
    except Exception as e:
        return {"detail": "Failed", "data": "Unable to update settings"}


@router.post("/update_settings")
async def update_settings(
    new_settings: NotificationDict,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    try:
        update_settings_task(new_settings.dict(), current_user.user_id, db)
        return {"detail": "Success", "data": "Settings updated successfully"}
    except Exception as e:
        return {"detail": "Failed", "data": "Unable to update settings"}
