from main import app
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from fastapi import status
from utils import *

client = TestClient(app)


def test_change_password_success(client, create_test_db):
    with patch("routers.settings.change_password_task") as mock_change_password_task:
        mock_change_password_task.return_value = {
            "detail": "Success",
            "data": "Password changed successfully",
        }
        response = client.post(
            "/settings/change_password",
            json={
                "current_password": "password",
                "new_password": "password1",
                "confirm_password": "password1",
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "detail": "Success",
            "data": "Password changed successfully",
        }


def test_change_password_fail(client, create_test_db):
    with patch("routers.settings.change_password_task") as mock_change_password_task:
        mock_change_password_task.return_value = {
            "detail": "Failed",
            "data": "Unable to change password",
        }
        response = client.post(
            "/settings/change_password",
            json={
                "current_password": "password",
                "new_password": "password1",
                "confirm_password": "password1",
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "detail": "Failed",
            "data": "Unable to change password",
        }


def test_get_settings_success(client, create_test_db):
    with patch("routers.settings.get_settings_task") as mock_get_settings_task:
        mock_get_settings_task.return_value = {
            "detail": "Success",
            "data": "data",
        }
        response = client.get(
            "/settings/get_settings",
        )
        assert response.status_code == status.HTTP_200_OK


def test_get_settings_fail(client, create_test_db):
    with patch("routers.settings.get_settings_task") as mock_get_settings_task:
        mock_get_settings_task.return_value = {
            "detail": "Failed",
            "data": "Unable to get settings",
        }
        response = client.get(
            "/settings/get_settings",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "detail": "Failed",
            "data": "Unable to get settings",
        }


def test_update_settings_success(client, create_test_db):
    with patch("routers.settings.update_settings_task") as mock_update_settings_task:
        mock_update_settings_task.return_value = {
            "detail": "Success",
            "data": "Settings updated successfully",
        }
        response = client.post(
            "/settings/update_settings",
            json={
                "newsletter": True,
                "email_notification": True,
                "discord_webhook": "",
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "detail": "Success",
            "data": "Settings updated successfully",
        }


def test_update_settings_fail(client, create_test_db):
    with patch("routers.settings.update_settings_task") as mock_update_settings_task:
        mock_update_settings_task.return_value = {
            "detail": "Failed",
            "data": "Unable to update settings",
        }
        response = client.post(
            "/settings/update_settings",
            json={
                "newsletter": True,
                "email_notification": True,
                "discord_webhook": "",
            },
        )
        assert response.status_code == status.HTTP_200_OK
