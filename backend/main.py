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
from utils import GOOGLE_SECRET, HOST, PORT, REDIS_HOST, APP_ENV, REPLICATE_API_TOKEN, CLOUDFLARE_METADATA, REDIS_PORT
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import time
from utils import PrometheusMiddleware, metrics, logger, r2_client
from dotenv import load_dotenv
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import multiprocess
from prometheus_client import generate_latest, CollectorRegistry, CONTENT_TYPE_LATEST, Gauge, Counter, make_asgi_app
import logging
from sqlalchemy.orm import Session
from botocore.exceptions import ClientError

load_dotenv()

APP_ENV = os.getenv("APP_ENV")
APP_NAME = os.environ.get("APP_NAME", "fastapi-backend")
EXPOSE_PORT = os.environ.get("EXPOSE_PORT", 8000)
OTLP_GRPC_ENDPOINT = os.environ.get("OTLP_GRPC_ENDPOINT", "http://tempo:4317")


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()



if APP_ENV == "production":
    app = FastAPI(docs_url=None, redoc_url=None)
    resource = Resource.create(
        attributes={"service.name": APP_NAME, "compose_service": APP_NAME}
    )
    tracer = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer)
    tracer.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=OTLP_GRPC_ENDPOINT)))
    LoggingInstrumentor().instrument(set_logging_format=True)
    FastAPIInstrumentor.instrument_app(app, tracer_provider=tracer)
    app.add_middleware(PrometheusMiddleware, app_name=APP_NAME)
else:
    app = FastAPI()


origins = [
    "https://localhost:3000",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://0.0.0.0:3000",
    "https://app.tnsr.ai",
    "http://app.tnsr.ai"
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
    with Session(engine) as db:
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
                "stem_seperation": "Audio Separation",
                "speech_enhancement": "Speech Enhancement",
                "transcription": "Transcription",
                "remove_background": "Remove Background",
                "job_initiated": "Job Initiated",
                "content_upload": "Uploading Content"
            }
            counter = 1
            for tag in all_tags:
                db.add(
                    models.Tags(
                        id = counter, tag=tag, readable=all_tags[tag], created_at=int(time.time())
                    )
                )
                counter += 1
            db.commit()


@app.on_event("startup")
async def startup():
    init_db()
    if APP_ENV == "production" or APP_ENV == "development":
        os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN
        try:
            r2_client.head_object(Bucket=CLOUDFLARE_METADATA, Key="srt_thumbnail.jpg")
            r2_client.head_object(Bucket=CLOUDFLARE_METADATA, Key="stem.jpg")
        except:
            r2_client.upload_file("./script_utils/srt_thumbnail.jpg", CLOUDFLARE_METADATA, "srt_thumbnail.jpg")
            r2_client.upload_file("./script_utils/stem.jpg", CLOUDFLARE_METADATA, "stem.jpg")
    redis_connection = redis.from_url(
        f"redis://{REDIS_HOST}:{REDIS_PORT}", encoding="utf-8", decode_responses=True
    )
    await FastAPILimiter.init(redis_connection)


@app.get("/", dependencies=[Depends(RateLimiter(times=60, seconds=60))])
async def root(req: Request):
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("get_root_endpoint"):
        logger.info(f"Request from {req.client.host}")
    return {"status": "Server is running"}


if APP_ENV == "production":
    def make_metrics_app():
        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)
        return make_asgi_app(registry=registry)

    metrics_app = make_metrics_app()
    app.mount("/metrics", metrics_app)

if __name__ == "__main__":
    if APP_ENV == "development":
        import uvicorn
        log_config = uvicorn.config.LOGGING_CONFIG 
        log_config["formatters"]["access"][
            "fmt"
        ] = "%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] [trace_id=%(otelTraceID)s span_id=%(otelSpanID)s resource.service.name=%(otelServiceName)s] - %(message)s"
        uvicorn.run("main:app", host=HOST, port=int(PORT), log_config=log_config)
    else:
        pass
