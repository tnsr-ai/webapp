import sys

sys.path.append("..")
import os
from utils import (
    REPLICATE_API_TOKEN,
    CLOUDFLARE_ACCESS_KEY,
    CLOUDFLARE_SECRET_KEY,
    CLOUDFLARE_ACCOUNT_ENDPOINT,
    CONTENT_EXPIRE,
    CLOUDFLARE_CONTENT,
    IMAGE_SUPERRES,
    IMAGE_DEBLURRING,
    IMAGE_DENOISING,
    IMAGE_FACERESTORATION,
    IMAGE_REMOVEBG,
    IMAGE_COLORIZER,
)
import boto3, botocore
import replicate
import redis
import models
from database import engine, SessionLocal


def generated_presigned(key, bucket):
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
            ExpiresIn=604000,
        )
        return response
    except Exception as e:
        return None


class ReplicateImageProcessor:
    def __init__(self, config: dict):
        self.config = config
        self.output_path = None
        self.content_type = config["job_type"]
        self.content_id = config["job_data"]["content_id"]
        self.db = SessionLocal()
        self.table_type = {
            "video": models.Videos,
            "image": models.Images,
            "audio": models.Audios,
        }
        self.table = self.table_type[self.content_type]
        self.content_url = None
        self.output = None
        os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN

    def process(self):
        self.content_info = (
            self.db.query(self.table).filter(self.table.id == self.content_id).first()
        )
        self.content_url = generated_presigned(
            self.content_info.link, CLOUDFLARE_CONTENT
        )
        if self.content_url is None:
            return {"detail": "Failed", "data": "Unable to fetch content url"}
        if self.config["job_data"]["filters"]["super_resolution"]["active"]:
            self.output = replicate.run(
                IMAGE_SUPERRES,
                input={
                    "image": self.content_url,
                    "model_name": self.config["job_data"]["filters"][
                        "super_resolution"
                    ]["model"],
                    "seed": 1999,
                },
            )
            self.content_url = self.output
        if self.config["job_data"]["filters"]["deblur"]["active"]:
            self.output = replicate.run(
                IMAGE_DEBLURRING,
                input={
                    "image": self.content_url,
                    "seed": 1999,
                },
            )
            self.content_url = self.output
        if self.config["job_data"]["filters"]["denoise"]["active"]:
            self.output = replicate.run(
                IMAGE_DENOISING,
                input={
                    "image": self.content_url,
                    "seed": 1999,
                },
            )
            self.content_url = self.output
        if self.config["job_data"]["filters"]["face_restoration"]["active"]:
            self.output = replicate.run(
                IMAGE_FACERESTORATION,
                input={
                    "image": self.content_url,
                    "seed": 1999,
                },
            )
            self.content_url = self.output
        if self.config["job_data"]["filters"]["colorizer"]["active"]:
            self.output = replicate.run(
                IMAGE_COLORIZER,
                input={
                    "image": self.content_url,
                    "seed": 1999,
                },
            )
            self.content_url = self.output
        if self.config["job_data"]["filters"]["remove_bg"]["active"]:
            self.output = replicate.run(
                IMAGE_REMOVEBG,
                input={
                    "image": self.content_url,
                    "seed": 1999,
                },
            )
            self.content_url = self.output
        print(self.content_url)


if __name__ == "__main__":
    config = {
        "job_type": "image",
        "job_data": {
            "content_id": 1,
            "content_type": "image",
            "filters": {
                "super_resolution": {
                    "active": True,
                    "model": "SuperRes 2x v1 (Faster)",
                },
                "deblur": {"active": False},
                "denoise": {"active": False},
                "face_restoration": {"active": False},
                "colorizer": {"active": True},
                "remove_bg": {"active": False},
            },
        },
    }
    rep = ReplicateImageProcessor(config)
    rep.process()
