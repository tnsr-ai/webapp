from fastapi import FastAPI, Depends, Request
import models
from database import engine, SessionLocal
from routers import (
    auth,
    dashboard,
    upload,
    content,
    settings,
    jobs,
    options,
    machines,
    billing,
    dev,
)
import os
import redis.asyncio as redis
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from utils import GOOGLE_SECRET, HOST, PORT, REDIS_HOST, APP_ENV
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import time
from utils import PrometheusMiddleware, metrics, setting_otlp, logger

APP_NAME = os.environ.get("APP_NAME", "fastapi-backend")
EXPOSE_PORT = os.environ.get("EXPOSE_PORT", 8000)
OTLP_GRPC_ENDPOINT = os.environ.get("OTLP_GRPC_ENDPOINT", "http://tempo:4317")


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


app = FastAPI()

if APP_ENV != "github" and APP_ENV != "development":
    app.add_middleware(PrometheusMiddleware, app_name=APP_NAME)
    setting_otlp(app, APP_NAME, OTLP_GRPC_ENDPOINT)


origins = [
    "https://localhost:3000",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://0.0.0.0:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SessionMiddleware, secret_key=GOOGLE_SECRET)

models.Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(upload.router)
app.include_router(content.router)
app.include_router(settings.router)
app.include_router(jobs.router)
app.include_router(options.router)
app.include_router(machines.router)
app.include_router(billing.router)
app.include_router(dev.router)


def init_db():
    db = SessionLocal()
    if db.query(models.Tags).first() is None:
        all_tags = {
            "original": "Original",
            "super_resolution": "Super Resolution",
            "video_deblurring": "Video Deblurring",
            "video_denoising": "Video Denoising",
            "face_restoration": "Face Restoration",
            "bw_to_color": "B/W To Color",
            "slow_motion": "Slow Motion",
            "video_interpolation": "Video Interpolation",
            "video_deinterlacing": "Video Deinterlacing",
            "image_deblurring": "Image Deblurring",
            "image_denoising": "Image Denoising",
            "stem_seperation": "Stem Seperation",
            "speech_enhancement": "Speech Enhancement",
            "transcription": "Transcription",
            "remove_background": "Remove Background",
        }
        for tag in all_tags:
            db.add(
                models.Tags(
                    tag=tag, readable=all_tags[tag], created_at=int(time.time())
                )
            )
        db.commit()
    db.close()


@app.on_event("startup")
async def startup():
    init_db()
    redis_connection = redis.from_url(
        f"redis://{REDIS_HOST}", encoding="utf-8", decode_responses=True
    )
    await FastAPILimiter.init(redis_connection)


@app.get("/", dependencies=[Depends(RateLimiter(times=60, seconds=60))])
async def root(req: Request):
    logger.info(f"Request from {req.client.host}")
    return {"status": "Server is running"}


app.add_route("/metrics", metrics)


if __name__ == "__main__":
    import uvicorn

    log_config = uvicorn.config.LOGGING_CONFIG  # set timezone to UTC
    log_config["formatters"]["access"][
        "fmt"
    ] = "%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] [trace_id=%(otelTraceID)s span_id=%(otelSpanID)s resource.service.name=%(otelServiceName)s] - %(message)s"
    uvicorn.run("main:app", host=HOST, port=int(PORT), log_config=log_config)
