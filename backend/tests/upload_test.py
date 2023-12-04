from main import app
from fastapi.testclient import TestClient
from unittest.mock import patch
from fastapi import status
from utils import *
from routers.upload import UploadDict, Upload, IndexContent

client = TestClient(app)


def test_generate_presigned_post(client, create_test_db):
    with patch("routers.upload.throttler.consume") as mock_consume, patch(
        "routers.upload.generate_signed_url_task"
    ) as mock_generate_signed_url_task:
        mock_consume.return_value = True
        mock_generate_signed_url_task.return_value = {
            "detail": "Success",
            "data": {
                "signed_url": "https://samplesignedurl.com",
                "filename": "unique_filename.mp4",
                "md5": "md5_hash",
            },
        }
        response = client.post(
            "/upload/generate_presigned_post",
            json=UploadDict(
                filename="unique_filename.mp4",
                filetype="video.mp4",
                md5="md5_hash",
                filesize=1000000,
            ).dict(),
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json() == {
            "detail": "Success",
            "data": {
                "signed_url": "https://samplesignedurl.com",
                "filename": "unique_filename.mp4",
                "md5": "md5_hash",
            },
        }


def test_generate_presigned_post_rate_limited(client, create_test_db):
    with patch("routers.upload.throttler.consume") as mock_consume, patch(
        "routers.upload.generate_signed_url_task"
    ) as mock_generate_signed_url_task:
        mock_consume.return_value = False
        response = client.post(
            "/upload/generate_presigned_post",
            json=UploadDict(
                filename="unique_filename.mp4",
                filetype="video.mp4",
                md5="md5_hash",
                filesize=1000000,
            ).dict(),
        )
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS


def test_generate_presigned_post_storagelimited(client, create_test_db):
    with patch("routers.upload.throttler.consume") as mock_consume, patch(
        "routers.upload.generate_signed_url_task"
    ) as mock_generate_signed_url_task:
        mock_consume.return_value = True
        mock_generate_signed_url_task.return_value = {
            "detail": "Failed",
            "data": "Storage limit exceeded",
        }
        response = client.post(
            "/upload/generate_presigned_post",
            json=UploadDict(
                filename="unique_filename.mp4",
                filetype="video.mp4",
                md5="md5_hash",
                filesize=1000000,
            ).dict(),
        )
        assert response.status_code == status.HTTP_507_INSUFFICIENT_STORAGE


def test_indexfile_success(client, create_test_db):
    with patch("routers.upload.throttler.consume") as mock_consume, patch(
        "routers.upload.index_media_task"
    ) as mock_index_media_task:
        mock_consume.return_value = True
        mock_index_media_task.return_value = {
            "detail": "Success",
            "data": {
                "filename": "unique_filename.mp4",
                "filetype": "video.mp4",
                "md5": "md5_hash",
                "filesize": 1000000,
                "duration": 100,
                "width": 1920,
                "height": 1080,
                "bitrate": 1000000,
                "framerate": 30,
                "audio_bitrate": 128000,
                "audio_sample_rate": 44100,
                "audio_channels": 2,
                "created_at": 1620124800,
            },
        }
        response = client.post(
            "/upload/indexfile",
            json=IndexContent(
                config={"data": {}},
                processtype="video",
                md5="md5_hash",
            ).dict(),
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json() == {
            "status_code": 201,
            "detail": "File indexed",
            "headers": None,
        }


def test_indexfile_rate_limited(client, create_test_db):
    with patch("routers.upload.throttler.consume") as mock_consume, patch(
        "routers.upload.index_media_task"
    ) as mock_index_media_task:
        mock_consume.return_value = False
        response = client.post(
            "/upload/indexfile",
            json=IndexContent(
                config={"data": {}},
                processtype="video",
                md5="md5_hash",
            ).dict(),
        )
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS


def test_indexfile_failed(client, create_test_db):
    with patch("routers.upload.throttler.consume") as mock_consume, patch(
        "routers.upload.index_media_task"
    ) as mock_index_media_task:
        mock_consume.return_value = True
        mock_index_media_task.return_value = {
            "detail": "Failed",
            "data": "File not found",
        }
        response = client.post(
            "/upload/indexfile",
            json=IndexContent(
                config={"data": {}},
                processtype="video",
                md5="md5_hash",
            ).dict(),
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
