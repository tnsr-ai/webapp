from celery import Celery
from fastapi import FastAPI, Depends, HTTPException
import models
from sqlalchemy.orm import Session
import os
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
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from utils import throttler, GOOGLE_SECRET


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


app = FastAPI()

origins = ["https://localhost:3000", "http://localhost:3000"]

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


@app.get("/")
async def root(db: Session = Depends(get_db)):
    if throttler.consume(identifier="user_id"):
        return {"message": "Server is running"}
    raise HTTPException(status_code=429, detail="Too Many Requests")


if __name__ == "__main__":
    import uvicorn
    import ssl

    uvicorn.run(
        "main:app",
        host="localhost",
        port=8000,
        ssl_version=ssl.PROTOCOL_SSLv23,
        ssl_keyfile="./localhost-key.pem",
        ssl_certfile="./localhost.pem",
        reload=True,
    )
