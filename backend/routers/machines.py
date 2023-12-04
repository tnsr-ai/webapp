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
from utils import throttler
load_dotenv()


router = APIRouter(
    prefix="/machines",
    tags=["machines"],
    responses={404: {"description": "Not found"}}
)

models.Base.metadata.create_all(bind=engine)

@celeryapp.task
def delete_instance_celery(job_id:int, machine_id:int, key:str) -> None:
    pass