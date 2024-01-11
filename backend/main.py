from fastapi import FastAPI, Depends, Request, Response, HTTPException
import models
from sqlalchemy.orm import Session
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
import redis.asyncio as redis
from datetime import datetime, timedelta
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from typing import Annotated, Any, Callable, TypeVar
from utils import GOOGLE_SECRET, HOST, PORT, REDIS_HOST, REDIS_PORT
from prometheus_client import make_asgi_app
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


app = FastAPI()

origins = [
    "https://localhost:3000",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
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


@app.on_event("startup")
async def startup():
    redis_connection = redis.from_url(
        "redis://127.0.0.1", encoding="utf-8", decode_responses=True
    )
    await FastAPILimiter.init(redis_connection)


@app.get("/", dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def root(req: Request):
    return {"status": "Server is running"}


metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=HOST,
        port=int(PORT),
        reload=True,
    )
