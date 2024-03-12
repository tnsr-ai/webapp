from main import app
from fastapi.testclient import TestClient
from unittest.mock import patch
from fastapi import status
from utils import *
from routers.upload import UploadDict, Upload, IndexContent
import pytest
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)


@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client


def test_generate_presigned_post(client, create_test_db):
    with patch(
        "routers.upload.generate_signed_url_task"
    ) as mock_generate_signed_url_task:
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


def test_generate_presigned_post_storagelimited(client, create_test_db):
    with patch(
        "routers.upload.generate_signed_url_task"
    ) as mock_generate_signed_url_task:
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