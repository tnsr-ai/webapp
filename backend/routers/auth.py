import sys

sys.path.append("..")

from typing import Optional, Annotated
from fastapi import Depends, HTTPException, APIRouter, Response, Header, Request
from fastapi.responses import HTMLResponse
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from pydantic import BaseModel
from starlette import status
from datetime import timedelta
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from starlette.requests import Request
from fastapi_sso.sso.google import GoogleSSO
from jose import jwt
import json
import time
import ast
import os
import secrets
import redis
import copy
from celeryworker import celeryapp
from fastapi_limiter.depends import RateLimiter
from utils import (
    get_hashed_password,
    verify_password,
    create_access_token,
    create_refresh_token,
)
from utils import (
    JWT_ALGORITHM,
    JWT_SECRET,
    JWT_REFRESH_SECRET,
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_REFRESH_TOKEN_EXPIRE_MINUTES,
    REDIS_HOST,
    REDIS_PORT,
    TNSR_DOMAIN,
    GOOGLE_REDIRECT_URI,
)
from utils import isValidEmail, hide_email, logger
from utils import registration_email, forgotpassword_email
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(
    prefix="/auth", tags=["auth"], responses={401: {"user": "Not authorized"}}
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


class CreateUser(BaseModel):
    firstname: str
    lastname: str
    email: str
    password: str


class ForgotPassword(BaseModel):
    email: str


class GoogleUser(BaseModel):
    name: str
    email: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: int
    refreshVersion: int
    accessVersion: int


class RefreshToken(BaseModel):
    refreshToken: str


class User(BaseModel):
    detail: str
    data: dict
    token_type: str
    access_token: str
    refreshToken: str


def user_exists(email: str, db: db_dependency):
    user = db.query(models.Users).filter(models.Users.email == email).first()
    if not user:
        return False
    return True


def authenticate_user(email: str, password: str, db: db_dependency):
    user = db.query(models.Users).filter(models.Users.email == email).first()
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return True


def minutes_to_delta(minutes: int):
    return int(timedelta(minutes=minutes).total_seconds())


oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)


def get_current_user(db: db_dependency, token: str = Depends(oauth2_bearer)):
    try:
        if len(token.split(".")) != 3:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                headers={"WWW-Authenticate": "Bearer"},
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    payload = ast.literal_eval(payload["sub"])
    get_user = db.query(models.Users).filter(models.Users.id == payload["id"]).first()
    if not get_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not a valid user ",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if (
        get_user.refreshVersion != payload["refreshVersion"]
        or get_user.accessVersion != payload["accessVersion"]
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token_data = TokenData(
        user_id=payload["id"],
        refreshVersion=payload["refreshVersion"],
        accessVersion=payload["accessVersion"],
    )
    return token_data


def get_current_user_refresh(db: db_dependency, token: str = Depends(oauth2_bearer)):
    try:
        payload = jwt.decode(token, JWT_REFRESH_SECRET, algorithms=[JWT_ALGORITHM])
        payload = ast.literal_eval(payload["sub"])
        get_user = (
            db.query(models.Users).filter(models.Users.id == payload["id"]).first()
        )
        if not get_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if get_user.refreshVersion != payload["refreshVersion"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token_data = TokenData(
            user_id=payload["id"],
            refreshVersion=payload["refreshVersion"],
            accessVersion=payload["accessVersion"],
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_data


def create_user_task(
    firstname: str,
    lastname: str,
    email: str,
    password: str,
    user_tier: str,
    google_login: bool,
    created_at: int,
    db: db_dependency,
):
    try:
        email_token = {
            "token": secrets.token_urlsafe(32),
            "expires": created_at + 172800,
        }
        create_user_model = models.Users(
            first_name=firstname,
            last_name=lastname,
            email=email,
            hashed_password=get_hashed_password(password),
            user_tier=user_tier,
            verified=False,
            google_login=google_login,
            created_at=created_at,
            email_token=json.dumps(email_token),
            refreshVersion=1,
            accessVersion=1,
        )
        db.add(create_user_model)
        db.commit()
        db.refresh(create_user_model)
        if create_user_model.user_tier == "free":
            storage_limit = 1073741824 * 2
        elif create_user_model.user_tier == "standard":
            storage_limit = 1073741824 * 20
        elif create_user_model.user_tier == "deluxe":
            storage_limit = 1073741824 * 100
        else:
            storage_limit = 1073741824 * 2
        create_dashboard_model = models.Dashboard(
            user_id=int(create_user_model.id),
            video_processed=0,
            audio_processed=0,
            image_processed=0,
            downloads=0,
            uploads=0,
            storage_used=0,
            storage_limit=storage_limit,
            gpu_usage=0,
            storage_json="""{"video":0, "audio":0, "image":0}""",
            created_at=created_at,
            updated_at=0,
        )
        db.add(create_dashboard_model)
        db.commit()
        db.refresh(create_dashboard_model)
        return {
            "detail": "Success",
            "data": {
                "id": int(create_user_model.id),
                "email_token": email_token["token"],
            },
        }
    except Exception as e:
        return {"detail": "Failed", "data": str(e)}


@celeryapp.task(name="routers.auth.send_email_task")
def send_email_task(name: int, verification_link: str, receiver_email: str):
    email_status = registration_email(name, verification_link, receiver_email)
    if email_status == False:
        return {"detail": "Failed", "data": "Failed to send email"}
    return {"detail": "Success", "data": "Email sent successfully"}


@router.post(
    "/signup",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimiter(times=20, seconds=60))],
)
async def create_user(
    response: Response,
    create_user_request: CreateUser,
    db: Session = Depends(get_db),
):
    if user_exists(create_user_request.email, db):
        logger.error(f"Email already exists - {hide_email(create_user_request.email)}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already exists"
        )
    if isValidEmail(create_user_request.email) == False:
        logger.error(f"Invalid email - {create_user_request.email}")
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Invalid email"
        )
    if len(create_user_request.password) < 8:
        logger.error(f"Password too short")
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="Password must be at least 8 characters",
        )
    if len(create_user_request.password) > 50:
        logger.error(f"Password too long")
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="Password must be less than 50 characters",
        )
    if (
        len(create_user_request.firstname) == 0
        or len(create_user_request.lastname) == 0
    ):
        logger.error(f"First name or last name empty")
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="First name and last name cannot be empty",
        )
    if (
        len(create_user_request.firstname) > 50
        or len(create_user_request.lastname) > 50
    ):
        logger.error(f"First name or last name too long")
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="First name and last name cannot be more than 50 characters",
        )
    result = create_user_task(
        create_user_request.firstname,
        create_user_request.lastname,
        create_user_request.email,
        create_user_request.password,
        "free",
        False,
        int(time.time()),
        db,
    )
    if result["detail"] == "Failed":
        logger.error(
            f"Failed to create user - {hide_email(create_user_request.email)}, data - {result['data']}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result["data"]
        )
    get_user = (
        db.query(models.Users).filter(models.Users.id == result["data"]["id"]).first()
    )
    content = {
        "id": int(get_user.id),
        "firstname": get_user.first_name,
        "lastname": get_user.last_name,
        "email": get_user.email,
    }
    token_payload = {
        "id": get_user.id,
        "refreshVersion": get_user.refreshVersion,
        "accessVersion": get_user.accessVersion,
    }
    access_token = create_access_token(
        token_payload, expires_delta=timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refreshToken = create_refresh_token(
        token_payload, expires_delta=timedelta(minutes=JWT_REFRESH_TOKEN_EXPIRE_MINUTES)
    )
    content.update(
        {
            "refreshToken": refreshToken,
            "access_token": access_token,
            "token_type": "bearer",
        }
    )
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=minutes_to_delta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
        path="/",
        secure=False,
        samesite="lax",
    )
    response.set_cookie(
        key="refreshToken",
        value=refreshToken,
        max_age=minutes_to_delta(minutes=JWT_REFRESH_TOKEN_EXPIRE_MINUTES),
        path="/",
        secure=False,
        samesite="lax",
    )
    logger.info(f"User created - {hide_email(create_user_request.email)}")
    verification_link = f"{TNSR_DOMAIN}/verifyemail/?user_id={get_user.id}&email_token={result['data']['email_token']}"
    send_email_task.delay(
        create_user_request.firstname, verification_link, create_user_request.email
    )
    logger.info(f"Email sent to {hide_email(create_user_request.email)}")
    return {
        "data": content,
        "detail": "Success",
        "token_type": "bearer",
        "access_token": access_token,
        "refreshToken": refreshToken,
    }


def login_user_task(email: str, password: str, db: db_dependency):
    try:
        user = authenticate_user(email, password, db)
        if user is False:
            return {"detail": "Failed", "data": "Invalid email or password"}
        if not user:
            return {"detail": "Failed", "data": "Invalid email or password"}
        get_user = db.query(models.Users).filter(models.Users.email == email).first()
        return {"detail": "Success", "data": int(get_user.id)}
    except Exception as e:
        return {"detail": "Failed", "data": str(e)}


@router.post(
    "/login",
    response_model=User,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(times=20, seconds=60))],
)
async def login_user(
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
):
    result = login_user_task(form_data.username, form_data.password, db)
    if result["detail"] == "Failed":
        logger.error(
            f"Failed to login user - {hide_email(form_data.username)}, data - {result['data']}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=result["data"]
        )
    user = db.query(models.Users).filter(models.Users.id == result["data"]).first()
    user.refreshVersion += 1
    user.accessVersion += 1
    db.commit()
    db.refresh(user)
    content = {
        "id": int(user.id),
        "firstname": user.first_name,
        "lastname": user.last_name,
        "email": user.email,
    }
    token_payload = {
        "id": user.id,
        "refreshVersion": user.refreshVersion,
        "accessVersion": user.accessVersion,
    }
    access_token = create_access_token(
        token_payload, expires_delta=timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refreshToken = create_refresh_token(
        token_payload, expires_delta=timedelta(minutes=JWT_REFRESH_TOKEN_EXPIRE_MINUTES)
    )
    content.update(
        {
            "refreshToken": refreshToken,
            "access_token": access_token,
            "token_type": "bearer",
        }
    )
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=minutes_to_delta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
        path="/",
        secure=False,
        samesite="lax",
    )
    response.set_cookie(
        key="refreshToken",
        value=refreshToken,
        max_age=minutes_to_delta(minutes=JWT_REFRESH_TOKEN_EXPIRE_MINUTES),
        path="/",
        secure=False,
        samesite="lax",
    )
    logger.info(f"User logged in - {hide_email(form_data.username)}")
    return {
        "data": content,
        "detail": "Success",
        "token_type": "bearer",
        "access_token": access_token,
        "refreshToken": refreshToken,
    }


def logout_user_task(user_id: int, db: db_dependency):
    try:
        user = db.query(models.Users).filter(models.Users.id == user_id).first()
        if not user:
            return {"detail": "Failed", "data": "Invalid email or password"}
        user.refreshVersion += 1
        user.accessVersion += 1
        db.commit()
        return {"detail": "Success", "data": "Logged out successfully"}
    except Exception as e:
        return {"detail": "Failed", "data": str(e)}


@router.get(
    "/logout",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(times=20, seconds=60))],
)
async def logout_user(
    response: Response,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    result = logout_user_task(current_user.user_id, db)
    if result["detail"] == "Failed":
        logger.error(
            f"Failed to logout user - {current_user.user_id}, data - {result['data']}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=result["data"]
        )
    response.delete_cookie(key="refreshToken")
    response.delete_cookie(key="access_token")
    logger.info(f"User logged out - {current_user.user_id}")
    return {"data": "Logout Successfully", "detail": "Success"}


def verify_user_task(
    user_id: int, token: str, exp_time: int, rd: redis.Redis, db: db_dependency
):
    try:
        redis_key = "accessToken_" + str(user_id)
        if rd.exists(redis_key):
            rd_content = rd.get(redis_key)
            rd_content = json.loads(rd_content)
            if rd_content["token"] == token:
                return {"detail": "Success", "data": rd_content}
            else:
                rd.delete(redis_key)
        user = db.query(models.Users).filter(models.Users.id == user_id).first()
        if not user:
            return {"detail": "Failed", "data": "Invalid email or password"}
        content = {
            "id": int(user.id),
            "firstname": user.first_name,
            "lastname": user.last_name,
            "email": user.email,
            "verified": user.verified,
        }
        rd_content = copy.copy(content)
        rd_content["token"] = token
        rd.set(redis_key, json.dumps(rd_content))
        rd.expire(redis_key, exp_time - 100)
        return {"detail": "Success", "data": content}
    except Exception as e:
        return {"detail": "Failed", "data": str(e)}


@router.get(
    "/verify",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(times=20, seconds=60))],
)
async def check_user(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
    authorization: Optional[str] = Header(None),
    rd: redis.Redis = Depends(get_redis),
):
    auth_token = authorization.split(" ")[1]
    if len(auth_token.split(".")) != 3:
        logger.error(f"Invalid access token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = jwt.decode(auth_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    result = verify_user_task(
        current_user.user_id, auth_token, int(payload["exp"]), rd, db
    )
    if result["detail"] == "Failed":
        logger.error(
            f"Failed to verify user - {current_user.user_id}, data - {result['data']}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=result["data"]
        )
    content = result["data"]
    logger.info(f"User verified - {current_user.user_id}")
    return {"data": content, "detail": "Success"}


def refresh_user_task(user_id: int, db: db_dependency):
    try:
        user = db.query(models.Users).filter(models.Users.id == user_id).first()
        if not user:
            return {"detail": "Failed", "data": "Invalid email or password"}
        token = create_access_token(
            {
                "id": user.id,
                "refreshVersion": user.refreshVersion,
                "accessVersion": user.accessVersion + 1,
            }
        )
        newRefreshToken = create_refresh_token(
            {
                "id": user.id,
                "refreshVersion": user.refreshVersion + 1,
                "accessVersion": user.accessVersion + 1,
            }
        )
        user.accessVersion += 1
        db.commit()
        return {
            "detail": "Success",
            "data": {"access_token": token, "refreshToken": newRefreshToken},
        }
    except Exception as e:
        return {"detail": "Failed", "data": str(e)}


@router.get(
    "/refresh",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(times=10, seconds=60))],
)
async def check_user_refresh(
    response: Response,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user_refresh),
):
    result = refresh_user_task(current_user.user_id, db)
    if result["detail"] == "Failed":
        logger.error(
            f"Failed to refresh user - {current_user.user_id}, data - {result['data']}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=result["data"]
        )
    accessToken = result["data"]["access_token"]
    refreshToken = result["data"]["refreshToken"]
    content = {
        "access_token": accessToken,
        "refreshToken": refreshToken,
        "token_type": "bearer",
    }
    response.set_cookie(
        key="access_token",
        value=accessToken,
        max_age=minutes_to_delta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
        path="/",
        secure=False,
        samesite="lax",
    )
    response.set_cookie(
        key="refreshToken",
        value=refreshToken,
        max_age=minutes_to_delta(minutes=JWT_REFRESH_TOKEN_EXPIRE_MINUTES),
        path="/",
        secure=False,
        samesite="lax",
    )
    logger.info(f"User refreshed - {current_user.user_id}")
    return {"data": content, "detail": "Success"}


# Google Auth Code

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_SECRET_ID")
GOOGLE_DISCOVERY_URL = os.getenv("GOOGLE_DISCOVERY_URL")

google_sso = GoogleSSO(
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    redirect_uri=GOOGLE_REDIRECT_URI,
)


@router.get("/google/login", dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def google_login():
    logger.info(f"Google login initiated")
    return await google_sso.get_login_redirect(
        params={"prompt": "consent", "access_type": "offline"}
    )


def google_callback_task(user_data: dict, db: db_dependency):
    try:
        user = (
            db.query(models.Users)
            .filter(models.Users.email == user_data["email"])
            .first()
        )
        if not user:
            created_at = int(time.time())
            user = models.Users(
                first_name=user_data["display_name"],
                last_name="",
                email=user_data["email"],
                hashed_password="",
                user_tier="free",
                verified=True,
                google_login=True,
                created_at=created_at,
                refreshVersion=1,
                accessVersion=1,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            create_dashboard_model = models.Dashboard(
                user_id=int(user.id),
                video_processed=0,
                audio_processed=0,
                image_processed=0,
                downloads=0,
                uploads=0,
                storage_used=0,
                storage_limit=0,
                gpu_usage=0,
                storage_json="""{'video':0, 'audio':0, 'image':0}""",
                created_at=created_at,
                updated_at=0,
            )
            db.add(create_dashboard_model)
            db.commit()
            db.refresh(create_dashboard_model)
        logger.info(f"Google login success - {hide_email(user_data['email'])}")
        return {"detail": "Success", "data": int(user.id)}
    except Exception as e:
        logger.error(
            f"Google login failed - {hide_email(user_data['email'])}, data - {str(e)}"
        )
        return {"detail": "Failed", "data": str(e)}


@router.get("/google/callback")
async def google_callback(
    response: Response, request: Request, db: Session = Depends(get_db)
):
    user = await google_sso.verify_and_process(request)
    if user is None:
        logger.error(f"Failed to fetch user information")
        raise HTTPException(401, detail="Failed to fetch user information")
    user_data = {
        "id": user.id,
        "picture": user.picture,
        "display_name": user.display_name,
        "email": user.email,
        "provider": user.provider,
    }
    result = google_callback_task(user_data, db)
    if result["detail"] == "Failed":
        logger.error(
            f"Google login failed - {hide_email(user_data['email'])}, data - {result['data']}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=result["data"]
        )
    user_id = result["data"]
    user_db = db.query(models.Users).filter(models.Users.id == user_id).first()
    token_payload = {
        "id": user_db.id,
        "refreshVersion": user_db.refreshVersion,
        "accessVersion": user_db.accessVersion,
    }
    access_token = create_access_token(
        token_payload, expires_delta=timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refreshToken = create_refresh_token(
        token_payload, expires_delta=timedelta(minutes=JWT_REFRESH_TOKEN_EXPIRE_MINUTES)
    )
    content = {
        "id": int(user.id),
        "firstname": user.first_name,
        "lastname": user.last_name,
        "email": user.email,
    }
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=minutes_to_delta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
        path="/",
        secure=False,
        samesite="lax",
    )
    response.set_cookie(
        key="refreshToken",
        value=refreshToken,
        max_age=minutes_to_delta(minutes=JWT_REFRESH_TOKEN_EXPIRE_MINUTES),
        path="/",
        secure=False,
        samesite="lax",
    )
    content.update(
        {
            "refreshToken": refreshToken,
            "access_token": access_token,
            "access_token_max": minutes_to_delta(
                minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES
            ),
            "refreshToken_max": minutes_to_delta(
                minutes=JWT_REFRESH_TOKEN_EXPIRE_MINUTES
            ),
            "token_type": "bearer",
        }
    )
    content_str = json.dumps(content)
    logger.info(f"Google login success - {hide_email(user_data['email'])}")
    return HTMLResponse(
        content=f"""
      <script>
          window.opener.postMessage({content_str}, "{os.getenv("DOMAIN")}");
          window.close();
      </script>
      """
    )


def forgot_password_task(name: str, verification_link: str, receiver_email: str):
    try:
        email_status = forgotpassword_email(name, verification_link, receiver_email)
        if email_status == False:
            return {"detail": "Failed", "data": "Failed to send email"}
        return {"detail": "Success", "data": f"Email sent to {receiver_email}"}
    except Exception as e:
        return {"detail": "Failed", "data": str(e)}


@router.post(
    "/forgotpassword",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(times=20, seconds=60))],
)
async def forgot_password(
    response: Response, forgot_model: ForgotPassword, db: Session = Depends(get_db)
):
    user = (
        db.query(models.Users).filter(models.Users.email == forgot_model.email).first()
    )
    if not user:
        logger.error(f"Email not found - {forgot_model.email}")
        return {"detail": "Failed", "data": "Email not found"}
    forgotpassword_token = {
        "token": secrets.token_urlsafe(32),
        "expires": int(time.time()) + 10800,
    }
    user.forgotpassword_token = json.dumps(forgotpassword_token)
    db.commit()
    result = forgot_password_task(
        user.first_name,
        TNSR_DOMAIN + "/auth/forgotpassword/" + forgotpassword_token["token"],
        user.email,
    )
    if result["detail"] == "Failed":
        logger.error(
            f"Failed to send email - {forgot_model.email}, data - {result['data']}"
        )
        return {"detail": "Failed", "data": result["data"]}
    logger.info(f"Forgot password email sent - {forgot_model.email}")
    return {"detail": "Success", "data": result["data"]}


def verify_email_task(
    user_id: int, email_token: str, rd: redis.Redis, db: db_dependency
):
    try:
        user = db.query(models.Users).filter(models.Users.id == user_id).first()
        if not user:
            return {"detail": "Failed", "data": "User not found"}
        user_email_token = json.loads(user.email_token)
        if user_email_token["token"] != email_token:
            return {"detail": "Failed", "data": "Invalid token"}
        if user_email_token["expires"] < int(time.time()):
            return {"detail": "Failed", "data": "Token expired"}
        user.email_token = None
        user.verified = True
        db.commit()
        redis_key = "accessToken_" + str(user_id)
        rd.delete(redis_key)
        return {"detail": "Success", "data": "Email verified successfully"}
    except Exception as e:
        return {"detail": "Failed", "data": str(e)}


@router.get(
    "/verifyemail",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimiter(times=20, seconds=60))],
)
async def verify_email(
    user_id: int,
    email_token: str,
    db: Session = Depends(get_db),
    rd: redis.Redis = Depends(get_redis),
):
    result = verify_email_task(user_id, email_token, rd, db)
    if result["detail"] == "Failed":
        logger.error(f"Failed to verify email - {user_id}, data - {result['data']}")
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=result["data"]
        )
    logger.info(f"Email verified - {user_id}")
    return {"detail": "Success", "data": result["data"]}
