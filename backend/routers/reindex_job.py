import base64
import json
import sys

sys.path.append("..")
import time
import models
import os
from database import SessionLocal
import models
import pathlib
import requests
from uuid import uuid4
import shutil
import ast 
from script_utils.util import *
from utils import r2_client
from utils import CLOUDFLARE_CONTENT, CLOUDFLARE_ACCESS_KEY, CLOUDFLARE_SECRET_KEY, CLOUDFLARE_METADATA, CLOUDFLARE_ACCOUNT_ENDPOINT
import boto3, botocore
from script_utils.util import lower_resolution_image, create_thumbnail_image, thumbnail_upload


def reindex_image_job(job_config, content_url):
    db = SessionLocal()
    user = db.query(models.Users).filter(models.Users.id == job_config["user_id"]).first()
    if user is None:
        return {"detail": "Failed", "data": "User not found"}
    user_dashboard = (
        db.query(models.Dashboard)
        .filter(models.Dashboard.user_id == job_config["user_id"])
        .first()
    )
    content_data = (
            db.query(models.Content)
            .filter(
                models.Content.id == job_config["content_id"]
            )
            .filter(models.Content.user_id == job_config["user_id"])
            .filter(models.Content.content_type == job_config["job_type"])
            .first()
        )
    job_data = (
        db.query(models.Jobs)
        .join(models.Content, models.Jobs.content_id == models.Content.id)
        .filter(models.Jobs.job_id == job_config["job_id"])
        .filter(models.Content.user_id == job_config["user_id"])
        .first()
    )
    pathlib.Path(f'thumbnail/{job_config["user_id"]}').mkdir(parents=True, exist_ok=True)
    content_title = os.path.splitext(content_data.title)[0] + "_" + str(uuid4()) + content_url.split(".")[-1]
    content_path = f'thumbnail/{job_config["user_id"]}/{os.path.splitext(content_title)[0]}.jpg'
    response = requests.get(content_url, stream=True)
    with open(content_path, 'wb') as out_file:
        shutil.copyfileobj(response.raw, out_file)
    del response
    thumbnail_path = f'thumbnail/{job_config["user_id"]}/{content_title}_thumbnail.jpg'
    key_file = f'{job_config["user_id"]}/{content_title}'
    presigned_url = r2_client.generate_presigned_url(
        ClientMethod="put_object",
        Params={
            "Bucket": os.getenv("BUCKET_NAME", CLOUDFLARE_CONTENT),
            "Key": key_file,
        },
        ExpiresIn=int(os.getenv("EXPIRE_TIME", 3600)),
    )
    with open(content_path, 'rb') as image:
        files = {'file': (content_path, image)}
        response = requests.put(presigned_url, data=image)
    if response.status_code != 200:
        return {"detail": "Failed", "data": "File Index Failed"}
    s3 = boto3.client(
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
    obj_data = s3.head_object(Bucket=CLOUDFLARE_CONTENT, Key=key_file)
    response = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": CLOUDFLARE_CONTENT, "Key": key_file},
        ExpiresIn=3600,
    )
    s3.close()
    img_size, width, height = lower_resolution_image(response, thumbnail_path)
    create_thumbnail_image(thumbnail_path)
    thumbnail_upload(thumbnail_path)
    content_data.link = key_file
    content_data.size = int(img_size)
    content_data.content_type = "image"
    content_data.resolution = f"{width}x{height}"
    content_data.thumbnail = thumbnail_path
    content_data.status = "completed"
    content_data.updated_at = int(time.time())
    # Update User Dashboard Stats
    user_dashboard.image_processed += 1
    user_dashboard.uploads += int(content_data.size)
    user_dashboard.storage_used += int(content_data.size)
    storage_json = ast.literal_eval(user_dashboard.storage_json)
    storage_json["image"] = float(bytes_to_mb(content_data.size)) + float(
        storage_json["image"]
    )
    user_dashboard.storage_json = json.dumps(storage_json)
    # Update Job Data
    job_data.job_status = "Completed"
    job_data.job_process = "completed"
    job_data.job_key = False
    job_data.updated_at = int(time.time())

    db.add(user_dashboard)
    db.add(content_data)
    db.add(job_data)
    db.commit()
    db.close()
    os.remove(content_path)
    os.remove(thumbnail_path)
    return {"detail": "Success", "data": "Image Indexed"}
