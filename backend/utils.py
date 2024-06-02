import jwt
from dotenv import load_dotenv
import os
from typing import Union, Any
from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
import boto3, botocore
from email.mime.image import MIMEImage
import pystache
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import re
import ssl
import time
from typing import Tuple
import logging as logger
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import REGISTRY, Counter, Gauge, Histogram
from prometheus_client.openmetrics.exposition import (
    CONTENT_TYPE_LATEST,
    generate_latest,
)
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Match
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR
from starlette.types import ASGIApp
from celeryworker import celeryapp
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
import requests
import models
import redis
import subprocess
import json


load_dotenv()
APP_ENV = os.getenv("APP_ENV")
if APP_ENV == "development":
    load_dotenv(dotenv_path=".env.development")
elif APP_ENV == "github":
    load_dotenv(dotenv_path=".env.github")
elif APP_ENV == "docker":
    load_dotenv(dotenv_path=".env.docker")
elif APP_ENV == "production":
    load_dotenv(dotenv_path=".env")

ENV = os.getenv("ENV")

CONTENT_EXPIRE = int(os.getenv("CONTENT_EXPIRE"))

# Cloudflare Credentials
CLOUDFLARE_ACCOUNT_ENDPOINT = os.getenv("CLOUDFLARE_ACCOUNT_ENDPOINT")
CLOUDFLARE_ACCESS_KEY = os.getenv("CLOUDFLARE_ACCESS_KEY")
CLOUDFLARE_SECRET_KEY = os.getenv("CLOUDFLARE_SECRET_KEY")
CLOUDFLARE_CONTENT = os.getenv("CLOUDFLARE_CONTENT")
CLOUDFLARE_METADATA = os.getenv("CLOUDFLARE_METADATA")
CLOUDFLARE_EXPIRE_TIME = os.getenv("CLOUDFLARE_EXPIRE_TIME")

# JWT Credentials
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_REFRESH_SECRET = os.getenv("JWT_REFRESH_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES"))
JWT_REFRESH_TOKEN_EXPIRE_MINUTES = eval(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_MINUTES"))
JWT_AUTH_TOKEN = os.getenv("JWT_AUTH_TOKEN")

# Google Credentials
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_SECRET_ID = os.getenv("GOOGLE_SECRET_ID")
GOOGLE_DISCOVERY_URL = os.getenv("GOOGLE_DISCOVERY_URL")
GOOGLE_SECRET = os.getenv("GOOGLE_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

# Website Credentials
TNSR_DOMAIN = os.getenv("TNSR_DOMAIN")
TNSR_BACKEND_DOMAIN = os.getenv("TNSR_BACKEND_DOMAIN")

# Database Credentials
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_USERNAME = os.getenv("POSTGRES_USERNAME")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DATABASE = os.getenv("POSTGRES_DATABASE")

# Redis Credentials
REDIS_BROKER = os.getenv("REDIS_BROKER")
REDIS_BACKEND = os.getenv("REDIS_BACKEND")
REDIS_PORT = int(os.getenv("REDIS_PORT"))
REDIS_HOST = str(os.getenv("REDIS_HOST"))

# Grafana Credentials
LOKI_URL = os.getenv("LOKI_URL")
LOKI_USERNAME = os.getenv("LOKI_USERNAME")
LOKI_PASSWORD = os.getenv("LOKI_PASSWORD")

# Crypto Credentials
CRYPTO_TOKEN = os.getenv("CRYPTO_TOKEN")

# Email Credentials
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = os.getenv("SMTP_PORT")
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

# Stripe Credentials
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY")

# Openexchange Credentials
OPENEXCHANGERATES_API_KEY = os.getenv("OPENEXCHANGERATES_API_KEY")

# FastAPI Config
HOST = os.getenv("HOST")
PORT = os.getenv("PORT")
API_KEY_NAME = "access_token"
API_KEY = os.getenv("METRICS_API_KEY")

# Replicate
try:
    REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
    GPU_PROVIDER = os.getenv("GPU_PROVIDER")
    CUDA = os.getenv("CUDA")
except:
    REPLICATE_API_TOKEN = "REPLICATE_API_TOKEN"
    GPU_PROVIDER = "vast,runpod"
    CUDA = "12.0,12.1,12.2,12.3,12.4"

if GPU_PROVIDER == None:
    GPU_PROVIDER = "vast,runpod"
if CUDA == None:
    CUDA = "12.0,12.1,12.2,12.3,12.4"

GPU_PROVIDER = GPU_PROVIDER.split(",")
CUDA = [float(x) for x in CUDA.split(",")]


STORAGE_LIMITS = {
    "free": 2 * 1024**3,
    "standard": 20 * 1024**3,
    "deluxe": 100 * 1024**3,
}

USER_TIER = {
    "free": {
        "video": {
            "size": STORAGE_LIMITS["free"],
            "width": 1920,
            "height": 1080,
            "formats": ["mp4", "mov", "mkv", "webm"],
            "duration": 600,
            "max_filters": 2,
        },
        "audio": {
            "size": STORAGE_LIMITS["free"],
            "formats": ["mp3", "wav", "m4v"],
            "duration": 600,
            "max_filters": 2,
        },
        "image": {
            "size": STORAGE_LIMITS["free"],
            "formats": ["png", "jpg", "jpeg", "webp"],
            "width": 1920,
            "height": 1080,
            "max_filters": 2,
        },
        "max_jobs": 100,
    },
    "standard": {
        "video": {
            "size": STORAGE_LIMITS["standard"],
            "width": 2560,
            "height": 1440,
            "formats": ["mp4", "mov", "mkv", "webm"],
            "duration": -1,
            "max_filters": 5,
        },
        "audio": {
            "size": STORAGE_LIMITS["standard"],
            "formats": ["mp3", "wav", "m4v"],
            "duration": -1,
            "max_filters": 5,
        },
        "image": {
            "size": STORAGE_LIMITS["standard"],
            "formats": ["png", "jpg", "jpeg", "webp"],
            "width": 2560,
            "height": 1440,
            "max_filters": 5,
        },
        "max_jobs": 5,
    },
    "deluxe": {
        "video": {
            "size": STORAGE_LIMITS["deluxe"],
            "width": 3840,
            "height": 2160,
            "formats": ["mp4", "mov", "mkv", "webm"],
            "duration": -1,
            "max_filters": 8,
        },
        "audio": {
            "size": STORAGE_LIMITS["deluxe"],
            "formats": ["mp3", "wav", "m4v"],
            "duration": -1,
            "max_filters": 8,
        },
        "image": {
            "size": STORAGE_LIMITS["deluxe"],
            "formats": ["png", "jpg", "jpeg", "webp"],
            "width": 3840,
            "height": 2160,
            "max_filters": 8,
        },
        "max_jobs": 10,
    },
}

MODELS_CONFIG = {
    "video": [
        {
            "super_resolution": {
                "model_name": {
                    "SuperRes 2x v1 (Faster)": {"input": 1, "output": 2},
                    "SuperRes 4x v1 (Faster)": {"input": 1, "output": 4},
                    "SuperRes 2x v2 (Slower, better result)": {"input": 1, "output": 2},
                    "SuperRes 4x v2 (Slower, better result)": {"input": 1, "output": 4},
                    "SuperRes Anime (For Animated content)": {"input": 1, "output": 1},
                },
                "tier": {
                    "free": {
                        "width": 1920,
                        "height": 1080,
                    },
                    "standard": {
                        "width": 2560,
                        "height": 1440,
                    },
                    "deluxe": {
                        "width": 3840,
                        "height": 2160,
                    },
                },
                "effect": "resolution",
            },
            "video_deblurring": {
                "model_name": {
                    "video_deblurring": {"input": 1, "output": 1},
                },
                "tier": {
                    "free": {
                        "width": 1920,
                        "height": 1080,
                    },
                    "standard": {
                        "width": 2560,
                        "height": 1440,
                    },
                    "deluxe": {
                        "width": 3840,
                        "height": 2160,
                    },
                },
                "effect": "resolution",
            },
            "video_denoising": {
                "model_name": {
                    "video_denoising": {"input": 1, "output": 1},
                },
                "tier": {
                    "free": {
                        "width": 1920,
                        "height": 1080,
                    },
                    "standard": {
                        "width": 2560,
                        "height": 1440,
                    },
                    "deluxe": {
                        "width": 3840,
                        "height": 2160,
                    },
                },
                "effect": "resolution",
            },
            "face_restoration": {
                "model_name": {
                    "face_restoration": {"input": 1, "output": 1},
                },
                "tier": {
                    "free": {
                        "width": 1920,
                        "height": 1080,
                    },
                    "standard": {
                        "width": 2560,
                        "height": 1440,
                    },
                    "deluxe": {
                        "width": 3840,
                        "height": 2160,
                    },
                },
                "effect": "resolution",
            },
            "bw_to_color": {
                "model_name": {
                    "bw_to_color": {"input": 1, "output": 1},
                },
                "tier": {
                    "free": {
                        "width": 1920,
                        "height": 1080,
                    },
                    "standard": {
                        "width": 2560,
                        "height": 1440,
                    },
                    "deluxe": {
                        "width": 3840,
                        "height": 2160,
                    },
                },
                "effect": "resolution",
            },
            "slow_motion": {
                "model_name": {
                    "2x": {"input": 1, "output": 2},
                    "4x": {"input": 1, "output": 4},
                },
                "tier": {
                    "free": {
                        "width": 1920,
                        "height": 1080,
                    },
                    "standard": {
                        "width": 2560,
                        "height": 1440,
                    },
                    "deluxe": {
                        "width": 3840,
                        "height": 2160,
                    },
                },
                "effect": "duration",
            },
            "video_interpolation": {
                "model_name": {
                    "video_interpolation": {"input": 1, "output": 2},
                },
                "tier": {
                    "free": {
                        "width": 1920,
                        "height": 1080,
                    },
                    "standard": {
                        "width": 2560,
                        "height": 1440,
                    },
                    "deluxe": {
                        "width": 3840,
                        "height": 2160,
                    },
                },
                "effect": "fps",
            },
            "video_deinterlacing": {
                "model_name": {
                    "video_deinterlacing": {"input": 1, "output": 1},
                },
                "tier": {
                    "free": {
                        "width": 1920,
                        "height": 1080,
                    },
                    "standard": {
                        "width": 2560,
                        "height": 1440,
                    },
                    "deluxe": {
                        "width": 3840,
                        "height": 2160,
                    },
                },
                "effect": "resolution",
            },
            "speech_enhancement": {
                "model_name": {
                    "speech_enhancement": {"input": 1, "output": 1},
                },
                "tier": {
                    "free": {
                        "width": 1920,
                        "height": 1080,
                    },
                    "standard": {
                        "width": 2560,
                        "height": 1440,
                    },
                    "deluxe": {
                        "width": 3840,
                        "height": 2160,
                    },
                },
                "effect": "audio",
            },
            "transcription": {
                "model_name": {
                    "transcription": {"input": 1, "output": 1},
                },
                "tier": {
                    "free": {
                        "width": 1920,
                        "height": 1080,
                    },
                    "standard": {
                        "width": 2560,
                        "height": 1440,
                    },
                    "deluxe": {
                        "width": 3840,
                        "height": 2160,
                    },
                },
                "effect": "srt",
            },
        }
    ],
    "audio": [
        {
            "stem_seperation": {
                "model_name": {
                    "stem_seperation": {"input": 1, "output": 1},
                },
                "tier": {
                    "free": {
                        "duration": 180,
                    },
                    "standard": {
                        "duration": -1,
                    },
                    "deluxe": {
                        "duration": -1,
                    },
                },
                "effect": "audio_files",
            },
            "speech_enhancement": {
                "model_name": {
                    "speech_enhancement": {"input": 1, "output": 1},
                },
                "tier": {
                    "free": {
                        "duration": 180,
                    },
                    "standard": {"duration": -1},
                    "deluxe": {"duration": -1},
                },
                "effect": "audio_files",
            },
            "transcription": {
                "model_name": {
                    "transcription": {"input": 1, "output": 1},
                },
                "tier": {
                    "free": {
                        "duration": 180,
                    },
                    "standard": {"duration": -1},
                    "deluxe": {"duration": -1},
                },
                "effect": "srt",
            },
        }
    ],
    "image": [
        {
            "super_resolution": {
                "model_name": {
                    "SuperRes 2x v1 (Faster)": {"input": 1, "output": 2},
                    "SuperRes 4x v1 (Faster)": {"input": 1, "output": 4},
                    "SuperRes 2x v2 (Slower, better result)": {"input": 1, "output": 2},
                    "SuperRes 4x v2 (Slower, better result)": {"input": 1, "output": 4},
                    "SuperRes Anime (For Animated content)": {"input": 1, "output": 1},
                },
                "tier": {
                    "free": {
                        "width": 1920,
                        "height": 1080,
                    },
                    "standard": {
                        "width": 2560,
                        "height": 1440,
                    },
                    "deluxe": {
                        "width": 3840,
                        "height": 2160,
                    },
                },
                "effect": "resolution",
            },
            "image_deblurring": {
                "model_name": {
                    "image_deblurring": {"input": 1, "output": 1},
                },
                "tier": {
                    "free": {
                        "width": 1920,
                        "height": 1080,
                    },
                    "standard": {
                        "width": 2560,
                        "height": 1440,
                    },
                    "deluxe": {
                        "width": 3840,
                        "height": 2160,
                    },
                },
                "effect": "resolution",
            },
            "image_denoising": {
                "model_name": {
                    "image_denoising": {"input": 1, "output": 1},
                },
                "tier": {
                    "free": {
                        "width": 1920,
                        "height": 1080,
                    },
                    "standard": {
                        "width": 2560,
                        "height": 1440,
                    },
                    "deluxe": {
                        "width": 3840,
                        "height": 2160,
                    },
                },
                "effect": "resolution",
            },
            "face_restoration": {
                "model_name": {
                    "face_restoration": {"input": 1, "output": 1},
                },
                "tier": {
                    "free": {
                        "width": 1920,
                        "height": 1080,
                    },
                    "standard": {
                        "width": 2560,
                        "height": 1440,
                    },
                    "deluxe": {
                        "width": 3840,
                        "height": 2160,
                    },
                },
                "effect": "resolution",
            },
            "bw_to_color": {
                "model_name": {
                    "bw_to_color": {"input": 1, "output": 1},
                },
                "tier": {
                    "free": {
                        "width": 1920,
                        "height": 1080,
                    },
                    "standard": {
                        "width": 2560,
                        "height": 1440,
                    },
                    "deluxe": {
                        "width": 3840,
                        "height": 2160,
                    },
                },
                "effect": "resolution",
            },
            "remove_background": {
                "model_name": {
                    "remove_background": {"input": 1, "output": 1},
                },
                "tier": {
                    "free": {
                        "width": 1920,
                        "height": 1080,
                    },
                    "standard": {
                        "width": 2560,
                        "height": 1440,
                    },
                    "deluxe": {
                        "width": 3840,
                        "height": 2160,
                    },
                },
                "effect": "resolution",
            },
        }
    ],
}

REDIS_KEY = {
    "Job Initiated": "job_initiated",
    "Super Resolution": "super_resolution",
    "Video Deblurring": "video_deblurring",
    "Video Denoising": "video_denoising",
    "Face Restoration": "face_restoration",
    "B/W to Color": "bw_to_color",
    "Slow Motion": "slow_motion",
    "Video Interpolation": "video_interpolation",
    "Video Deinterlacing": "video_deinterlacing",
    "Speech Enhancement": "speech_enhancement",
    "Transcription": "transcription",
}

INFO = Gauge("fastapi_app_info", "FastAPI application information.", ["app_name"])
REQUESTS = Counter(
    "fastapi_requests_total",
    "Total count of requests by method and path.",
    ["method", "path", "app_name"],
)
RESPONSES = Counter(
    "fastapi_responses_total",
    "Total count of responses by method, path and status codes.",
    ["method", "path", "status_code", "app_name"],
)
REQUESTS_PROCESSING_TIME = Histogram(
    "fastapi_requests_duration_seconds",
    "Histogram of requests processing time by path (in seconds)",
    ["method", "path", "app_name"],
)
EXCEPTIONS = Counter(
    "fastapi_exceptions_total",
    "Total count of exceptions raised by path and exception type",
    ["method", "path", "exception_type", "app_name"],
)
REQUESTS_IN_PROGRESS = Gauge(
    "fastapi_requests_in_progress",
    "Gauge of requests by method and path currently being processed",
    ["method", "path", "app_name"],
)

IMAGE_MODELS = {
    "super_resolution": {
        "model": "amitalokbera/imagesr:7a766d216010219a837e5b60bc85c5391329d4f22ce259c228e1c96491cc1c45",
        "params": {"model_name": "model"},
    },
    "image_deblurring": {
        "model": "amitalokbera/imagedeblurring:d92cbbbc9ce8b92db53f7a63f51b7f5eb055c0cfbb5fee0dc50ff0916d882af0"
    },
    "image_denoising": {
        "model": "amitalokbera/imagedenoising:a9948d49980973c800d11c5ed5e409422452a76b8ef2a532ce9cd0bed6355bd0"
    },
    "face_restoration": {
        "model": "amitalokbera/facerestoration:a66c794e36d8b0c7c0b6a3e716e9235ff1d7f15cf540781241c4a129519d6475"
    },
    "bw_to_color": {
        "model": "amitalokbera/imagecolorizer:0ed84ed3f6d18bad203b994d1827b5aad36ba5cbf1f0d7fdb729aeb31f1e30fe"
    },
    "remove_background": {
        "model": "amitalokbera/removebg:b0e5380f3d45f7f6b424557f3feb69f0eaa57bc42ac6643fd2b399118b2f7bb5"
    },
}

MODEL_COMPUTE = {
    "video": {
        "super_resolution": {
            "SuperRes 2x v1 (Faster)": 1400000,
            "SuperRes 4x v1 (Faster)": 700000,
            "SuperRes 2x v2 (Slower, better result)": 400000,
            "SuperRes 4x v2 (Slower, better result)": 200000,
            "SuperRes Anime (For Animated content)": 300000,
        },
        "video_deblurring": 800000,
        "video_denoising": 800000,
        "face_restoration": 2200000,
        "bw_to_color": 5500000,
        "slow_motion": {"2x": 1200000, "4x": 1000000},
        "video_interpolation": 10800000,
        "video_deinterlacing": 3000000,
        "speech_enhancement": 10800000,
        "transcription": 10800000,
    },
    "image": {
        "super_resolution": {
            "SuperRes 2x v1 (Faster)": 15,
            "SuperRes 4x v1 (Faster)": 15,
            "SuperRes 2x v2 (Slower, better result)": 18,
            "SuperRes 4x v2 (Slower, better result)": 20,
            "SuperRes Anime (For Animated content)": 15,
        },
        "image_deblurring": 15,
        "image_denoising": 15,
        "face_restoration": 15,
        "bw_to_color": 15,
        "remove_background": 15,
    },
    "audio": {"stem_seperation": 3, "speech_enhancement": 20, "transcription": 5},
}

SQLALCHEMY_DATABASE_URL = f"postgresql://{POSTGRES_USERNAME}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DATABASE}"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, pool_size=20, max_overflow=40, pool_pre_ping=True
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

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

r2_resource = boto3.resource(
    "s3",
    aws_access_key_id=CLOUDFLARE_ACCESS_KEY,
    aws_secret_access_key=CLOUDFLARE_SECRET_KEY,
    endpoint_url=CLOUDFLARE_ACCOUNT_ENDPOINT,
)


password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def allTags(id: bool = False):
    rd = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
    if id == False:
        rd_key = "all_tags"
    else:
        rd_key = "all_tags_id"
    if rd.exists(rd_key):
        return json.loads(rd.get(rd_key).decode("utf-8"))
    with Session(engine) as db:
        tags = db.query(models.Tags).all()
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


def get_hashed_password(password: str) -> str:
    return password_context.hash(password + JWT_AUTH_TOKEN)


def verify_password(password: str, hashed_pass: str) -> bool:
    return password_context.verify(password + JWT_AUTH_TOKEN, hashed_pass)


def isValidEmail(email: str) -> bool:
    pattern = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
    return re.match(pattern, email) is not None


def create_access_token(subject: Union[str, Any], expires_delta: int = None) -> str:
    if expires_delta is not None:
        expires_delta = datetime.utcnow() + expires_delta
    else:
        expires_delta = datetime.utcnow() + timedelta(
            minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expires_delta, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(subject: Union[str, Any], expires_delta: int = None) -> str:
    if expires_delta is not None:
        expires_delta = datetime.utcnow() + expires_delta
    else:
        expires_delta = datetime.utcnow() + timedelta(
            minutes=JWT_REFRESH_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expires_delta, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, JWT_REFRESH_SECRET, JWT_ALGORITHM)
    return encoded_jwt


def sql_dict(obj):
    result_dict = {x.name: getattr(obj, x.name) for x in obj.__table__.columns}
    return result_dict


def remove_key(data_list, key):
    for item in data_list:
        if key in item:
            del item[key]


def registration_email(name: str, verification: str, receiver_email: str):
    try:
        context = ssl.create_default_context()
        smtp_client = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context)
        smtp_client.login(SMTP_USERNAME, SMTP_PASSWORD)
        all_image_path = [
            Path() / "emailUtils/logo.png",
            Path() / "emailUtils/welcome.png",
            Path() / "emailUtils/twitter.png",
            Path() / "emailUtils/discord.png",
            Path() / "emailUtils/linkedin.png",
            Path() / "emailUtils/youtube.png",
        ]
        email_template = (Path() / "emailUtils/registration.html").read_text()
        template_params = {"name": name, "verification": verification}
        all_img = []
        for image_path in all_image_path:
            image = open(image_path, "rb")
            image_img = MIMEImage(image.read())
            image.close()
            image_img.add_header("Content-ID", f"<{image_path.name}>")
            image_img.add_header(
                "Content-Disposition", "inline", filename=image_path.name
            )
            template_params[image_path.stem] = image_path.name
            all_img.append(image_img)
        final_email_html = pystache.render(email_template, template_params)
        message = MIMEMultipart("related")
        message["Subject"] = "Email Verification"
        message["From"] = "welcome@tnsr.ai"
        message["To"] = receiver_email
        message.attach(MIMEText(final_email_html, "html"))
        for image in all_img:
            message.attach(image)
        smtp_client.sendmail("welcome@tnsr.ai", receiver_email, message.as_string())
        smtp_client.quit()
        return True
    except Exception as e:
        return str(e)


def forgotpassword_email(name: str, verification: str, receiver_email: str):
    try:
        context = ssl.create_default_context()
        smtp_client = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context)
        smtp_client.login(SMTP_USERNAME, SMTP_PASSWORD)
        all_image_path = [
            Path() / "emailUtils/logo.png",
            Path() / "emailUtils/forgot_password.png",
            Path() / "emailUtils/twitter.png",
            Path() / "emailUtils/discord.png",
            Path() / "emailUtils/linkedin.png",
            Path() / "emailUtils/youtube.png",
        ]
        email_template = (Path() / "emailUtils/forgot.html").read_text()
        template_params = {"name": name, "verification": verification}
        all_img = []
        for image_path in all_image_path:
            image = open(image_path, "rb")
            image_img = MIMEImage(image.read())
            image.close()
            image_img.add_header("Content-ID", f"<{image_path.name}>")
            image_img.add_header(
                "Content-Disposition", "inline", filename=image_path.name
            )
            template_params[image_path.stem] = image_path.name
            all_img.append(image_img)
        final_email_html = pystache.render(email_template, template_params)
        message = MIMEMultipart("related")
        message["Subject"] = "Reset Password"
        message["From"] = "support@tnsr.ai"
        message["To"] = receiver_email
        message.attach(MIMEText(final_email_html, "html"))
        for image in all_img:
            message.attach(image)
        smtp_client.sendmail("support@tnsr.ai", receiver_email, message.as_string())
        smtp_client.quit()
        return True
    except Exception as e:
        return False


def paymentinitiated_email(
    name: str,
    payment_status: str,
    credits: int,
    amount: str,
    receiver_email: str,
    invoice_id: int,
):
    try:
        context = ssl.create_default_context()
        smtp_client = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context)
        smtp_client.login(SMTP_USERNAME, SMTP_PASSWORD)
        all_image_path = [
            Path() / "emailUtils/logo.png",
            Path() / "emailUtils/payment_initiated.png",
            Path() / "emailUtils/twitter.png",
            Path() / "emailUtils/discord.png",
            Path() / "emailUtils/linkedin.png",
            Path() / "emailUtils/youtube.png",
        ]
        email_template = (Path() / "emailUtils/payment_initiated.html").read_text()
        template_params = {
            "name": name,
            "payment_status": payment_status,
            "credits": credits,
            "amount": amount,
            "payment_id": "#" + str(invoice_id + 1000),
        }
        all_img = []
        for image_path in all_image_path:
            image = open(image_path, "rb")
            image_img = MIMEImage(image.read())
            image.close()
            image_img.add_header("Content-ID", f"<{image_path.name}>")
            image_img.add_header(
                "Content-Disposition", "inline", filename=image_path.name
            )
            template_params[image_path.stem] = image_path.name
            all_img.append(image_img)
        final_email_html = pystache.render(email_template, template_params)
        message = MIMEMultipart("related")
        message["Subject"] = f"Payment Initiated for {amount}"
        message["From"] = "billing@tnsr.ai"
        message["To"] = receiver_email
        message.attach(MIMEText(final_email_html, "html"))
        for image in all_img:
            message.attach(image)
        smtp_client.sendmail("billing@tnsr.ai", receiver_email, message.as_string())
        smtp_client.quit()
        return True
    except Exception as e:
        return False


def paymentsuccessfull_email(name: str, credits: int, amount: str, receiver_email: str):
    try:
        context = ssl.create_default_context()
        smtp_client = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context)
        smtp_client.login(SMTP_USERNAME, SMTP_PASSWORD)
        all_image_path = [
            Path() / "emailUtils/logo.png",
            Path() / "emailUtils/payment_successfull.png",
            Path() / "emailUtils/twitter.png",
            Path() / "emailUtils/discord.png",
            Path() / "emailUtils/linkedin.png",
            Path() / "emailUtils/youtube.png",
        ]
        email_template = (Path() / "emailUtils/payment_successfull.html").read_text()
        template_params = {"name": name, "credits": credits, "amount": amount}
        all_img = []
        for image_path in all_image_path:
            image = open(image_path, "rb")
            image_img = MIMEImage(image.read())
            image.close()
            image_img.add_header("Content-ID", f"<{image_path.name}>")
            image_img.add_header(
                "Content-Disposition", "inline", filename=image_path.name
            )
            template_params[image_path.stem] = image_path.name
            all_img.append(image_img)
        final_email_html = pystache.render(email_template, template_params)
        message = MIMEMultipart("related")
        message["Subject"] = f"Payment Successfull for {amount}"
        message["From"] = "billing@tnsr.ai"
        message["To"] = receiver_email
        message.attach(MIMEText(final_email_html, "html"))
        for image in all_img:
            message.attach(image)
        smtp_client.sendmail("billing@tnsr.ai", receiver_email, message.as_string())
        smtp_client.quit()
        return True
    except Exception as e:
        print(e)
        return False


def paymentfailed_email(name: str, credits: int, amount: str, receiver_email: str):
    try:
        context = ssl.create_default_context()
        smtp_client = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context)
        smtp_client.login(SMTP_USERNAME, SMTP_PASSWORD)
        all_image_path = [
            Path() / "emailUtils/logo.png",
            Path() / "emailUtils/payment_failed.png",
            Path() / "emailUtils/twitter.png",
            Path() / "emailUtils/discord.png",
            Path() / "emailUtils/linkedin.png",
            Path() / "emailUtils/youtube.png",
        ]
        email_template = (Path() / "emailUtils/payment_failed.html").read_text()
        template_params = {"name": name, "credits": credits, "amount": amount}
        all_img = []
        for image_path in all_image_path:
            image = open(image_path, "rb")
            image_img = MIMEImage(image.read())
            image.close()
            image_img.add_header("Content-ID", f"<{image_path.name}>")
            image_img.add_header(
                "Content-Disposition", "inline", filename=image_path.name
            )
            template_params[image_path.stem] = image_path.name
            all_img.append(image_img)
        final_email_html = pystache.render(email_template, template_params)
        message = MIMEMultipart("related")
        message["Subject"] = f"Payment Failed for {amount}"
        message["From"] = "billing@tnsr.ai"
        message["To"] = receiver_email
        message.attach(MIMEText(final_email_html, "html"))
        for image in all_img:
            message.attach(image)
        smtp_client.sendmail("billing@tnsr.ai", receiver_email, message.as_string())
        smtp_client.quit()
        return True
    except Exception as e:
        return False


def presigned_get(key, bucket, rd, expire=None):
    try:
        if rd.exists(key):
            return rd.get(key).decode("utf-8")
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
        if expire is None:
            expire = CONTENT_EXPIRE - 60
        response = r2_client.generate_presigned_url(
            ClientMethod="get_object",
            Params={
                "Bucket": bucket,
                "Key": key,
            },
            ExpiresIn=CONTENT_EXPIRE,
        )
        rd.set(key, response)
        rd.expire(key, expire)
        return response
    except Exception as e:
        return None


def job_presigned_get(key, bucket):
    try:
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
                "Key": key,
            },
            ExpiresIn=259200,
        )
        return response
    except Exception as e:
        return None


def increase_and_round(number_val: int, credits: int) -> dict:
    if number_val == 0:
        return {"original": 0, "discounted": 0, "percentage": 0, "final_amt": 0}

    rounded_no = round(number_val)

    if rounded_no == 0:
        return {"original": 1, "discounted": 0, "percentage": 0, "final_amt": 1}

    discount = 0
    if 50 <= credits < 100:
        discount = 0.05
    elif 100 <= credits < 200:
        discount = 0.1
    elif 200 <= credits < 300:
        discount = 0.15
    elif 300 <= credits < 400:
        discount = 0.2
    elif 400 <= credits <= 500:
        discount = 0.25

    if discount == 0:
        return {
            "original": rounded_no,
            "discounted": 0,
            "percentage": 0,
            "final_amt": rounded_no,
        }

    return {
        "original": rounded_no,
        "discounted": round(rounded_no * (1 - discount)),
        "percentage": discount * 100,
        "final_amt": round(rounded_no * (1 - discount)),
    }


class PrometheusMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, app_name: str = "fastapi-app") -> None:
        super().__init__(app)
        self.app_name = app_name
        INFO.labels(app_name=self.app_name).inc()

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        method = request.method
        path, is_handled_path = self.get_path(request)

        if not is_handled_path:
            return await call_next(request)

        REQUESTS_IN_PROGRESS.labels(
            method=method, path=path, app_name=self.app_name
        ).inc()
        REQUESTS.labels(method=method, path=path, app_name=self.app_name).inc()
        before_time = time.perf_counter()
        try:
            response = await call_next(request)
        except BaseException as e:
            status_code = HTTP_500_INTERNAL_SERVER_ERROR
            EXCEPTIONS.labels(
                method=method,
                path=path,
                exception_type=type(e).__name__,
                app_name=self.app_name,
            ).inc()
            raise e from None
        else:
            status_code = response.status_code
            after_time = time.perf_counter()
            # retrieve trace id for exemplar
            span = trace.get_current_span()
            trace_id = trace.format_trace_id(span.get_span_context().trace_id)

            REQUESTS_PROCESSING_TIME.labels(
                method=method, path=path, app_name=self.app_name
            ).observe(after_time - before_time, exemplar={"TraceID": trace_id})
        finally:
            RESPONSES.labels(
                method=method,
                path=path,
                status_code=status_code,
                app_name=self.app_name,
            ).inc()
            REQUESTS_IN_PROGRESS.labels(
                method=method, path=path, app_name=self.app_name
            ).dec()

        return response

    @staticmethod
    def get_path(request: Request) -> Tuple[str, bool]:
        for route in request.app.routes:
            match, child_scope = route.matches(request.scope)
            if match == Match.FULL:
                return route.path, True

        return request.url.path, False


def metrics(request: Request) -> Response:
    return Response(
        generate_latest(REGISTRY), headers={"Content-Type": CONTENT_TYPE_LATEST}
    )


def setting_otlp(
    app: ASGIApp, app_name: str, endpoint: str, log_correlation: bool = True
) -> None:
    resource = Resource.create(
        attributes={"service.name": app_name, "compose_service": app_name}
    )
    tracer = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer)

    tracer.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))

    if log_correlation:
        LoggingInstrumentor().instrument(set_logging_format=True)

    FastAPIInstrumentor.instrument_app(app, tracer_provider=tracer)


def hide_email(email):
    local_part, domain = email.split("@")
    mask_length = len(local_part) - 2 if len(local_part) > 2 else len(local_part)
    show_length = (len(local_part) - mask_length) // 2
    if show_length > 0:
        masked_local = (
            local_part[:show_length] + "*" * mask_length + local_part[-show_length:]
        )
    else:
        masked_local = "*" * mask_length
    masked_email = masked_local + "@" + domain
    return masked_email


class EndpointFilter(logger.Filter):
    def filter(self, record: logger.LogRecord) -> bool:
        return record.getMessage().find("GET /metrics") == -1


logger.getLogger("uvicorn.access").addFilter(EndpointFilter())


@celeryapp.task(name="utils.delete_r2_object", acks_late=True)
def delete_r2_file(file_key: str, bucket: str):
    try:
        r2_resource_ = boto3.resource(
            "s3",
            aws_access_key_id=CLOUDFLARE_ACCESS_KEY,
            aws_secret_access_key=CLOUDFLARE_SECRET_KEY,
            endpoint_url=CLOUDFLARE_ACCOUNT_ENDPOINT,
        )
        bucket_ = r2_resource_.Bucket(bucket)
        bucket_.Object(file_key).delete()
        return True
    except Exception as e:
        return False


@celeryapp.task(name="utils.send_discord_update", acks_late=True)
def send_discord_update(job_id: int, user_id: int, status: str):
    try:
        with Session(engine) as db:
            context = ssl.create_default_context()
            smtp_client = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context)
            smtp_client.login(SMTP_USERNAME, SMTP_PASSWORD)
            user = db.query(models.Users).filter(models.Users.id == user_id).first()
            usersetting = (
                db.query(models.UserSetting)
                .filter(models.UserSetting.user_id == user_id)
                .first()
            )
            job = db.query(models.Jobs).filter(models.Jobs.job_id == job_id).first()
            content = (
                db.query(models.Content)
                .filter(models.Content.id == job.content_id)
                .all()
            )
            main_content = (
                db.query(models.Content)
                .filter(models.Content.id == content[0].id_related)
                .first()
            )
            all_tags = allTags(id=True)
            if usersetting is None:
                raise Exception("No User Found")
            if usersetting.discord_notification is False:
                return False
            all_filter = []
            for x in content:
                tags = (
                    db.query(models.ContentTags)
                    .filter(models.ContentTags.content_id == x.id)
                    .all()
                )
                for y in tags:
                    tag_name = all_tags[str(y.tag_id)]["readable"]
                    all_filter.append(tag_name)
            if status == "initiated":
                data = {
                    "content": f'🚀**Job Initiated**🚀 \n\nWe are pleased to inform you that your job has been successfully initiated!\n\n**ID:** {job.job_id}\n**Name:** {main_content.title}\n**Job Type:** {job.job_type.capitalize()}\n**Filters:** {", ".join(all_filter)}\n\nIf you did not initiate the job, please update your password and contact us immediately at admin@tnsr.ai\n\nBest Regards,\n[tnsr.ai](https://tnsr.ai)'
                }

                result = requests.post(usersetting.discord_webhook, json=data)
                if result.status_code == 204:
                    return True
                return False

            if status == "completed":
                data = {
                    "content": f'🎉 **Job Completed** 🎉\n\nWe are pleased to inform you that your job has been successfully completed!\n\n**ID:** {job.job_id}\n**Name:** {main_content.title}\n**Job Type:** {job.job_type.capitalize()}\n**Filters:** {", ".join(all_filter)}\n**Start Time:** {datetime.utcfromtimestamp(int(job.created_at)).strftime("%Y-%m-%d %H:%M:%S UTC")}\n**End Time:** {datetime.utcfromtimestamp(int(job.updated_at)).strftime("%Y-%m-%d %H:%M:%S UTC")}\n\nYou can access the processed content using the following link:[View Job]({f"{TNSR_DOMAIN}/{job.job_type}/{main_content.id}"})\n\nThank you for choosing our service! If you have any questions or need further assistance, please do not hesitate to contact us.\nBest regards,\n[tnsr.ai](https://tnsr.ai)'
                }

                result = requests.post(usersetting.discord_webhook, json=data)
                if result.status_code == 204:
                    return True
                return False

            if status == "failed":
                data = {
                    "content": "🚨 **Job Failed** 🚨\n\n"
                    "We regret to inform you that your job has encountered an issue and has failed.\n\n"
                    f"**ID:** {job.job_id}\n"
                    f"**Name:** {main_content.title}\n"
                    f"**Job Type:** {job.job_type.capitalize()}\n"
                    f'**Filters:** {", ".join(all_filter)}\n\n'
                    "Our team is currently investigating the issue to determine the cause and will take the necessary steps to ensure it does not occur in the future. We apologize for any inconvenience this may have caused.\n\n"
                    "Please reinitiate a new job at your earliest convenience. If you need any assistance with this process, please feel free to contact us at admin@tnsr.ai\n\n"
                    "Thank you for your understanding and patience.\n\n"
                    "Best regards,\n"
                    "[tnsr.ai](https://tnsr.ai)"
                }

                result = requests.post(usersetting.discord_webhook, json=data)
                if result.status_code == 204:
                    return True
                return False

            if status == "cancelled":
                data = {
                    "content": f"🚨 **Job Cancelled** 🚨\n\n"
                    "We regret to inform you that your job has been cancelled.\n\n"
                    f"**ID:** {job.job_id}\n"
                    f"**Name:** {main_content.title}\n"
                    f"**Job Type:** {job.job_type.capitalize()}\n"
                    f'**Filters:** {", ".join(all_filter)}\n\n'
                    "If you did not initiate the job cancellation, please update your password and contact us immediately at admin@tnsr.ai\n\n"
                    "Best regards,\n"
                    "[tnsr.ai](https://tnsr.ai)"
                }

                result = requests.post(usersetting.discord_webhook, json=data)
                if result.status_code == 204:
                    return True
                return False
    except Exception as e:
        return str(e)


@celeryapp.task(name="utils.job_email", acks_late=True)
def job_email(job_id: int, user_id: int, status: str):
    try:
        with Session(engine) as db:
            context = ssl.create_default_context()
            smtp_client = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context)
            smtp_client.login(SMTP_USERNAME, SMTP_PASSWORD)
            user = db.query(models.Users).filter(models.Users.id == user_id).first()
            usersetting = (
                db.query(models.UserSetting)
                .filter(models.UserSetting.user_id == user_id)
                .first()
            )
            job = db.query(models.Jobs).filter(models.Jobs.job_id == job_id).first()
            content = (
                db.query(models.Content)
                .filter(models.Content.id == job.content_id)
                .all()
            )
            main_content = (
                db.query(models.Content)
                .filter(models.Content.id == content[0].id_related)
                .first()
            )
            all_tags = allTags(id=True)
            if usersetting is None:
                raise Exception("No User Found")
            if usersetting.email_notification is False:
                return False
            if status == "initiated":
                email_template = (Path() / "emailUtils/job_initiated.html").read_text()
                all_filter = []
                for x in content:
                    tags = (
                        db.query(models.ContentTags)
                        .filter(models.ContentTags.content_id == x.id)
                        .all()
                    )
                    for y in tags:
                        tag_name = all_tags[str(y.tag_id)]["readable"]
                        all_filter.append(tag_name)
                template_params = {
                    "name": user.first_name,
                    "title": main_content.title,
                    "filters": ", ".join(all_filter),
                }
                all_image_path = [
                    Path() / "emailUtils/logo.png",
                    Path() / "emailUtils/job_initiated.png",
                    Path() / "emailUtils/twitter.png",
                    Path() / "emailUtils/discord.png",
                    Path() / "emailUtils/linkedin.png",
                    Path() / "emailUtils/youtube.png",
                ]
                all_img = []
                for image_path in all_image_path:
                    image = open(image_path, "rb")
                    image_img = MIMEImage(image.read())
                    image.close()
                    image_img.add_header("Content-ID", f"<{image_path.name}>")
                    image_img.add_header(
                        "Content-Disposition", "inline", filename=image_path.name
                    )
                    template_params[image_path.stem] = image_path.name
                    all_img.append(image_img)
                final_email_html = pystache.render(email_template, template_params)
                message = MIMEMultipart("related")
                message["Subject"] = f"Job Initiated - {job_id}"
                message["From"] = "updates@tnsr.ai"
                message["To"] = user.email
                message.attach(MIMEText(final_email_html, "html"))
                for image in all_img:
                    message.attach(image)
                smtp_client.sendmail("updates@tnsr.ai", user.email, message.as_string())
                smtp_client.quit()
                return True

            if status == "completed":
                email_template = (Path() / "emailUtils/job_success.html").read_text()
                all_filter = []
                for x in content:
                    tags = (
                        db.query(models.ContentTags)
                        .filter(models.ContentTags.content_id == x.id)
                        .all()
                    )
                    for y in tags:
                        tag_name = all_tags[str(y.tag_id)]["readable"]
                        all_filter.append(tag_name)
                template_params = {
                    "name": user.first_name,
                    "title": main_content.title,
                    "filters": ", ".join(all_filter),
                    "start_time": datetime.utcfromtimestamp(
                        int(job.created_at)
                    ).strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "end_time": datetime.utcfromtimestamp(int(job.updated_at)).strftime(
                        "%Y-%m-%d %H:%M:%S UTC"
                    ),
                    "link": f"{TNSR_DOMAIN}/{job.job_type}/{main_content.id}",
                }
                all_image_path = [
                    Path() / "emailUtils/logo.png",
                    Path() / "emailUtils/job_success.png",
                    Path() / "emailUtils/twitter.png",
                    Path() / "emailUtils/discord.png",
                    Path() / "emailUtils/linkedin.png",
                    Path() / "emailUtils/youtube.png",
                ]
                all_img = []
                for image_path in all_image_path:
                    image = open(image_path, "rb")
                    image_img = MIMEImage(image.read())
                    image.close()
                    image_img.add_header("Content-ID", f"<{image_path.name}>")
                    image_img.add_header(
                        "Content-Disposition", "inline", filename=image_path.name
                    )
                    template_params[image_path.stem] = image_path.name
                    all_img.append(image_img)
                final_email_html = pystache.render(email_template, template_params)
                message = MIMEMultipart("related")
                message["Subject"] = f"Job Completed - {job_id}"
                message["From"] = "updates@tnsr.ai"
                message["To"] = user.email
                message.attach(MIMEText(final_email_html, "html"))
                for image in all_img:
                    message.attach(image)
                smtp_client.sendmail("updates@tnsr.ai", user.email, message.as_string())
                smtp_client.quit()
                return True
            if status == "failed":
                email_template = (Path() / "emailUtils/job_failed.html").read_text()
                all_filter = []
                for x in content:
                    tags = (
                        db.query(models.ContentTags)
                        .filter(models.ContentTags.content_id == x.id)
                        .all()
                    )
                    for y in tags:
                        tag_name = all_tags[str(y.tag_id)]["readable"]
                        all_filter.append(tag_name)
                template_params = {
                    "name": user.first_name,
                    "title": main_content.title,
                    "filters": ", ".join(all_filter),
                }
                all_image_path = [
                    Path() / "emailUtils/logo.png",
                    Path() / "emailUtils/job_failed.png",
                    Path() / "emailUtils/twitter.png",
                    Path() / "emailUtils/discord.png",
                    Path() / "emailUtils/linkedin.png",
                    Path() / "emailUtils/youtube.png",
                ]
                all_img = []
                for image_path in all_image_path:
                    image = open(image_path, "rb")
                    image_img = MIMEImage(image.read())
                    image.close()
                    image_img.add_header("Content-ID", f"<{image_path.name}>")
                    image_img.add_header(
                        "Content-Disposition", "inline", filename=image_path.name
                    )
                    template_params[image_path.stem] = image_path.name
                    all_img.append(image_img)
                final_email_html = pystache.render(email_template, template_params)
                message = MIMEMultipart("related")
                message["Subject"] = f"Job Failed - {job_id}"
                message["From"] = "updates@tnsr.ai"
                message["To"] = user.email
                message.attach(MIMEText(final_email_html, "html"))
                for image in all_img:
                    message.attach(image)
                smtp_client.sendmail("updates@tnsr.ai", user.email, message.as_string())
                smtp_client.quit()
                return True
            if status == "cancelled":
                email_template = (Path() / "emailUtils/job_cancelled.html").read_text()
                all_filter = []
                for x in content:
                    tags = (
                        db.query(models.ContentTags)
                        .filter(models.ContentTags.content_id == x.id)
                        .all()
                    )
                    for y in tags:
                        tag_name = all_tags[str(y.tag_id)]["readable"]
                        all_filter.append(tag_name)
                template_params = {
                    "name": user.first_name,
                    "title": main_content.title,
                    "filters": ", ".join(all_filter),
                }
                all_image_path = [
                    Path() / "emailUtils/logo.png",
                    Path() / "emailUtils/job_cancelled.png",
                    Path() / "emailUtils/twitter.png",
                    Path() / "emailUtils/discord.png",
                    Path() / "emailUtils/linkedin.png",
                    Path() / "emailUtils/youtube.png",
                ]
                all_img = []
                for image_path in all_image_path:
                    image = open(image_path, "rb")
                    image_img = MIMEImage(image.read())
                    image.close()
                    image_img.add_header("Content-ID", f"<{image_path.name}>")
                    image_img.add_header(
                        "Content-Disposition", "inline", filename=image_path.name
                    )
                    template_params[image_path.stem] = image_path.name
                    all_img.append(image_img)
                final_email_html = pystache.render(email_template, template_params)
                message = MIMEMultipart("related")
                message["Subject"] = f"Job Cancelled - {job_id}"
                message["From"] = "updates@tnsr.ai"
                message["To"] = user.email
                message.attach(MIMEText(final_email_html, "html"))
                for image in all_img:
                    message.attach(image)
                smtp_client.sendmail("updates@tnsr.ai", user.email, message.as_string())
                smtp_client.quit()
                return True
    except Exception as e:
        return str(e)

def run_command(command: str):
    output = subprocess.run(command, shell=True, capture_output=True, text=True)
    ansi_escape = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
    cmd_output = ansi_escape.sub("", output.stdout)
    exit_code = output.returncode
    cmd_error = output.stderr
    return exit_code, cmd_output