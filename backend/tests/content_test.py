from main import app
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from fastapi import status
from utils import *

client = TestClient(app)


def test_get_content_success(client, create_test_db):
    with patch("routers.content.throttler.consume") as mock_consume, patch(
        "routers.content.get_content_table"
    ) as mock_get_content_table, patch(
        "routers.content.add_presigned"
    ) as mock_add_presigned, patch(
        "routers.content.filter_data"
    ) as mock_filter_data:
        mock_consume.return_value = True
        mock_get_content_table.return_value = {
            "detail": "Success",
            "data": ["all_result", "get_counts"],
        }
        mock_add_presigned.return_value = {
            "detail": "Success",
            "data": ["all_result", "get_counts"],
        }
        mock_filter_data.return_value = {
            "detail": "Success",
            "data": "data",
        }
        response = client.get(
            "/content/get_content?limit=10&offset=0&content_type=video&current_user=1"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "data": {"detail": "Success", "data": "data"},
            "detail": "Success",
            "total": "get_counts",
        }


def test_get_content_fail(client, create_test_db):
    with patch("routers.content.throttler.consume") as mock_consume, patch(
        "routers.content.get_content_table"
    ) as mock_get_content_table, patch(
        "routers.content.add_presigned"
    ) as mock_add_presigned, patch(
        "routers.content.filter_data"
    ) as mock_filter_data:
        mock_consume.return_value = True
        mock_get_content_table.return_value = {
            "detail": "Failed",
            "data": ["all_result", "get_counts"],
        }
        mock_add_presigned.return_value = {
            "detail": "Failed",
            "data": ["all_result", "get_counts"],
        }
        mock_filter_data.return_value = {
            "detail": "Failed",
            "data": "data",
        }
        response = client.get(
            "/content/get_content?limit=10&offset=0&content_type=video&current_user=1"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_get_content_list_success(client, create_test_db):
    with patch("routers.content.throttler.consume") as mock_consume, patch(
        "routers.content.get_content_list_celery"
    ) as mock_get_content_list_celery, patch(
        "routers.content.add_presigned"
    ) as mock_add_presigned, patch(
        "routers.content.filter_data"
    ) as mock_filter_data:
        mock_consume.return_value = True
        mock_get_content_list_celery.return_value = {
            "detail": "Success",
            "data": ["all_result", "get_counts"],
        }
        mock_add_presigned.return_value = {
            "detail": "Success",
            "data": ["all_result", "get_counts"],
        }
        mock_filter_data.return_value = {
            "detail": "Success",
            "data": "data",
        }
        response = client.get(
            "/content/get_content_list?limit=5&offset=0&content_type=video&current_user=1&content_id=1"
        )
        assert response.status_code == status.HTTP_200_OK


def test_get_content_list_fail(client, create_test_db):
    with patch("routers.content.throttler.consume") as mock_consume, patch(
        "routers.content.get_content_list_celery"
    ) as mock_get_content_list_celery, patch(
        "routers.content.add_presigned"
    ) as mock_add_presigned, patch(
        "routers.content.filter_data"
    ) as mock_filter_data:
        mock_consume.return_value = True
        mock_get_content_list_celery.return_value = {
            "detail": "Failed",
            "data": ["all_result", "get_counts"],
        }
        mock_add_presigned.return_value = {
            "detail": "Failed",
            "data": ["all_result", "get_counts"],
        }
        mock_filter_data.return_value = {
            "detail": "Failed",
            "data": "data",
        }
        response = client.get(
            "/content/get_content_list?limit=5&offset=0&content_type=video&current_user=1&content_id=1"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_download_content_success(client, create_test_db):
    with patch("routers.content.throttler.consume") as mock_consume, patch(
        "routers.content.download_content_task"
    ) as mock_download_content_task:
        mock_consume.return_value = True
        mock_download_content_task.return_value = {
            "detail": "Success",
            "data": ["all_result", "get_counts"],
        }
        response = client.get(
            "/content/download_content?content_id=1&current_user=1&content_type=video"
        )
        assert response.status_code == status.HTTP_200_OK


def test_download_content_fail(client, create_test_db):
    with patch("routers.content.throttler.consume") as mock_consume, patch(
        "routers.content.download_content_task"
    ) as mock_download_content_task:
        mock_consume.return_value = True
        mock_download_content_task.return_value = {
            "detail": "Failed",
            "data": ["all_result", "get_counts"],
        }
        response = client.get(
            "/content/download_content?content_id=1&current_user=1&content_type=video"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_download_complete_success(client, create_test_db):
    with patch("routers.content.throttler.consume") as mock_consume, patch(
        "routers.content.download_complete_task"
    ) as mock_download_complete_task:
        mock_consume.return_value = True
        mock_download_complete_task.return_value = {
            "detail": "Success",
            "data": ["all_result", "get_counts"],
        }
        response = client.get(
            "/content/download_complete?content_id=1&current_user=1&content_type=video"
        )
        assert response.status_code == status.HTTP_200_OK


def test_download_complete_fail(client, create_test_db):
    with patch("routers.content.throttler.consume") as mock_consume, patch(
        "routers.content.download_complete_task"
    ) as mock_download_complete_task:
        mock_consume.return_value = True
        mock_download_complete_task.return_value = {
            "detail": "Failed",
            "data": ["all_result", "get_counts"],
        }
        response = client.get(
            "/content/download_complete?content_id=1&current_user=1&content_type=video"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_rename_content_success(client, create_test_db):
    with patch("routers.content.throttler.consume") as mock_consume, patch(
        "routers.content.rename_content_celery"
    ) as mock_rename_content_celery:
        mock_consume.return_value = True
        mock_rename_content_celery.return_value = {
            "detail": "Success",
            "data": ["all_result", "get_counts"],
        }
        response = client.put("/content/rename-content/1/video/newtitle")
        assert response.status_code == status.HTTP_200_OK


def test_rename_content_fail(client, create_test_db):
    with patch("routers.content.throttler.consume") as mock_consume, patch(
        "routers.content.rename_content_celery"
    ) as mock_rename_content_celery:
        mock_consume.return_value = True
        mock_rename_content_celery.return_value = {
            "detail": "Failed",
            "data": ["all_result", "get_counts"],
        }
        response = client.put("/content/rename-content/1/video/newtitle")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
