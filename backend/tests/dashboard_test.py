from main import app
from fastapi.testclient import TestClient
from unittest.mock import patch
from fastapi import status
from utils import *

client = TestClient(app)


def test_get_status_success(client, create_test_db):
    with patch("routers.dashboard.throttler.consume") as mock_consume, patch(
        "routers.dashboard.dashboard_task"
    ) as mock_dashboard_task:
        mock_consume.return_value = True
        mock_dashboard_task.return_value = {
            "detail": "Success",
            "data": {
                "user_id": 1,
                "video_processed": 0,
                "audio_processed": 0,
                "image_processed": 0,
                "downloads": 0,
                "uploads": 0,
                "storage_used": 0,
                "storage_limit": 5368709120,
                "gpu_usage": 0,
                "storage_json": "{'video':0, 'audio':0, 'image':0}",
                "created_at": 1620124800,
            },
            "verified": True,
        }
        response = client.get("/dashboard/get_stats")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "detail": "Success",
            "data": {
                "user_id": 1,
                "video_processed": 0,
                "audio_processed": 0,
                "image_processed": 0,
                "downloads": "0 bytes",
                "uploads": "0 bytes",
                "storage_used": 0,
                "storage_limit": 5368709120,
                "gpu_usage": "0 Min",
                "storage_json": "{'video':0, 'audio':0, 'image':0}",
                "created_at": 1620124800,
                "storage": "0 bytes / 5 GB",
            },
            "verified": True,
        }


def test_get_status_rate_limited(client, create_test_db):
    with patch("routers.dashboard.throttler.consume") as mock_consume, patch(
        "routers.dashboard.dashboard_task"
    ) as mock_dashboard_task:
        mock_consume.return_value = False
        response = client.get("/dashboard/get_stats")
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert response.json() == {"detail": "Too Many Requests"}


def test_get_status_failed(client, create_test_db):
    with patch("routers.dashboard.throttler.consume") as mock_consume, patch(
        "routers.dashboard.dashboard_task"
    ) as mock_dashboard_task:
        mock_consume.return_value = True
        mock_dashboard_task.return_value = {"detail": "Failed", "data": "Error"}
        response = client.get("/dashboard/get_stats")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {"detail": "Error"}
