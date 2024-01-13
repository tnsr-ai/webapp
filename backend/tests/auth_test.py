from main import app
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from fastapi import status
from utils import *
from routers.auth import ForgotPassword
import time
from pydantic import BaseModel
import pytest
import models
import pytest


@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client


class GoogleData(BaseModel):
    id: int
    picture: str
    display_name: str
    email: str
    provider: str
    first_name: str
    last_name: str


@pytest.fixture(scope="function")
def test_user(test_db_session):
    db = test_db_session
    user = models.Users(
        first_name="firstname",
        last_name="lastname",
        email="admin@tnsr.ai",
        hashed_password=get_hashed_password("password"),
        user_tier="free",
        verified=False,
        google_login=False,
        created_at=int(time.time()),
        email_token="12345",
        refreshVersion=1,
        accessVersion=1,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    yield user
    db.delete(user)
    db.commit()


def test_create_user_success(client, create_test_db):
    with patch("routers.auth.user_exists") as mock_user_exists, patch(
        "routers.auth.send_email_task.delay"
    ) as mock_send_email:
        mock_user_exists.return_value = False
        create_user_data = {
            "firstname": "John",
            "lastname": "Doe",
            "email": "john.doe@example.com",
            "password": "securepassword123",
        }

        response = client.post("/auth/signup", json=create_user_data)
        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert response_data["detail"] == "Success"
        assert "data" in response_data
        assert response_data["data"]["firstname"] == "John"
        assert response_data["data"]["lastname"] == "Doe"
        assert response_data["data"]["email"] == "john.doe@example.com"

        assert "access_token" in response.cookies
        assert "refreshToken" in response.cookies

        mock_send_email.assert_called_once()
        args, kwargs = mock_send_email.call_args
        assert args[0] == "John"
        assert args[2] == "john.doe@example.com"


def test_create_user_existing_user(client, create_test_db):
    with patch("routers.auth.user_exists") as mock_user_exists:
        mock_user_exists.return_value = True
        create_user_data = {
            "firstname": "Jane",
            "lastname": "Smith",
            "email": "jane.smith@example.com",
            "password": "securepassword123",
        }
        response = client.post("/auth/signup", json=create_user_data)
        assert response.status_code == status.HTTP_409_CONFLICT
        assert response.json()["detail"] == "Email already exists"


def test_create_user_internal_error(client, create_test_db):
    with patch("routers.auth.user_exists") as mock_user_exists, patch(
        "routers.auth.create_user_task"
    ) as mock_create_user_task:
        mock_user_exists.return_value = False
        mock_create_user_task.return_value = {
            "detail": "Failed",
            "data": "Internal server error",
        }
        create_user_data = {
            "firstname": "Bob",
            "lastname": "Williams",
            "email": "bob.williams@example.com",
            "password": "securepassword123",
        }
        response = client.post("/auth/signup", json=create_user_data)
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json()["detail"] == "Internal server error"


def test_login_user_success(client, create_test_db):
    with patch("routers.auth.authenticate_user") as mock_authenticate_user, patch(
        "routers.auth.create_access_token"
    ) as mock_create_access_token, patch(
        "routers.auth.create_refresh_token"
    ) as mock_create_refresh_token:
        mock_authenticate_user.return_value = True
        mock_create_access_token.return_value = "access_token_example"
        mock_create_refresh_token.return_value = "refresh_token_example"
        login_data = {
            "username": "john.doe@example.com",
            "password": "securepassword123",
        }
        response = client.post("/auth/login", data=login_data)
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["detail"] == "Success"
        assert "access_token" in response_data
        assert "refreshToken" in response_data


def test_login_user_invalid_credentials(client, create_test_db):
    with patch("routers.auth.authenticate_user") as mock_authenticate_user:
        mock_authenticate_user.return_value = False
        login_data = {"username": "john.doe@example.com", "password": "wrongpassword"}

        response = client.post("/auth/login", data=login_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Invalid email or password"


def test_login_user_internal_error(client, create_test_db):
    with patch("routers.auth.login_user_task") as mock_login_user_task:
        mock_login_user_task.return_value = {
            "detail": "Failed",
            "data": "Internal server error",
        }

        login_data = {
            "username": "john.doe@example.com",
            "password": "securepassword123",
        }
        response = client.post("/auth/login", data=login_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Internal server error"


def test_logout_user_success(client, create_test_db):
    with patch("routers.auth.logout_user_task") as mock_logout_user_task:
        mock_logout_user_task.return_value = {
            "data": "Logout Successfully",
            "detail": "Success",
        }
        response = client.get("/auth/logout")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["detail"] == "Success"
        assert response.json()["data"] == "Logout Successfully"
        assert response.cookies.get("access_token") == None
        assert response.cookies.get("refreshToken") == None


def test_logout_user_failed(client, create_test_db):
    with patch("routers.auth.logout_user_task") as mock_logout_user_task:
        mock_logout_user_task.return_value = {
            "data": "Logout Successfully",
            "detail": "Failed",
        }
        response = client.get("/auth/logout")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_verify_success(client, create_test_db):
    with patch("routers.auth.verify_user_task") as mock_verify_user_task:
        mock_verify_user_task.return_value = {
            "detail": "Success",
            "data": {
                "id": 1,
                "firstname": "fname",
                "lastname": "lname",
                "email": "admin@admin.com",
                "verified": True,
            },
        }
        access_token = create_access_token(
            subject="testdata", expires_delta=timedelta(minutes=30)
        )
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }
        response = client.get("/auth/verify", headers=headers)
        assert response.status_code == status.HTTP_200_OK


def test_verify_failed(client, create_test_db):
    with patch("routers.auth.verify_user_task") as mock_verify_user_task:
        mock_verify_user_task.return_value = {
            "detail": "Success",
            "data": {
                "id": 1,
                "firstname": "fname",
                "lastname": "lname",
                "email": "admin@admin.com",
                "verified": True,
            },
        }
        headers = {
            "Authorization": "Bearer invalid_token",
            "Accept": "application/json",
        }
        response = client.get("/auth/verify", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_refresh_success(client, create_test_db):
    with patch("routers.auth.refresh_user_task") as mock_refresh_user_task:
        mock_refresh_user_task.return_value = {
            "data": {
                "access_token": "eyJ.eySJ9.HO_8jt_W7fQIFr0",
                "refreshToken": "eyJ.eySJ9.HO_8jt_W7fQIFr0",
                "token_type": "bearer",
            },
            "detail": "Success",
        }
        response = client.get("/auth/refresh")
        assert response.status_code == status.HTTP_200_OK
        assert "eyJ.eySJ9.HO_8jt_W7fQIFr0" in response.cookies["access_token"]
        assert "eyJ.eySJ9.HO_8jt_W7fQIFr0" in response.cookies["refreshToken"]


def test_refresh_failed(client, create_test_db):
    with patch("routers.auth.refresh_user_task") as mock_refresh_user_task:
        mock_refresh_user_task.return_value = {
            "data": {
                "access_token": "eyJ.eySJ9.HO_8jt_W7fQIFr0",
                "refreshToken": "eyJ.eySJ9.HO_8jt_W7fQIFr0",
                "token_type": "bearer",
            },
            "detail": "Failed",
        }
        response = client.get("/auth/refresh")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_google_login_success(client, create_test_db):
    redirect_url = "https://example.com/redirect"
    with patch(
        "routers.auth.google_sso.get_login_redirect", return_value=redirect_url
    ) as mock_login_redirect:
        response = client.get("/auth/google/login")
        assert response.status_code == status.HTTP_200_OK
        assert response.text == f'"{redirect_url}"'


def test_google_callback_success(client, create_test_db):
    with patch(
        "routers.auth.google_sso.verify_and_process"
    ) as mock_verify_and_process, patch(
        "routers.auth.google_callback_task"
    ) as mock_google_callback_task, patch(
        "routers.auth.create_access_token"
    ) as mock_create_access_token, patch(
        "routers.auth.create_refresh_token"
    ) as mock_create_refresh_token:
        mock_verify_and_process.return_value = GoogleData(
            id=1,
            picture="pic_link",
            display_name="admin",
            email="admin@email.com",
            provider="google",
            first_name="admin",
            last_name="admin",
        )
        mock_google_callback_task.return_value = {"detail": "Success", "data": 1}
        mock_create_access_token.return_value = "eyJ.eySJ9.HO_8jt_W7fQIFr0"
        mock_create_refresh_token.return_value = "eyJ.eySJ9.HO_8jt_W7fQIFr0"
        response = client.get("/auth/google/callback")
        assert response.status_code == status.HTTP_200_OK
        assert "window.opener.postMessage" in response.text


def test_forgot_password_success(client, test_user):
    forgot_model = ForgotPassword(email=test_user.email)
    with patch("routers.auth.forgot_password_task") as mock_forgot_password_task, patch(
        "os.getenv", return_value="https://example.com"
    ) as mock_getenv:
        mock_forgot_password_task.return_value = {
            "detail": "Success",
            "data": f"Email sent to {test_user.email}",
        }
        response = client.post("/auth/forgotpassword", json=forgot_model.dict())
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["detail"] == "Success"
        assert response.json()["data"] == f"Email sent to {test_user.email}"


def test_forgot_password_failed(client):
    forgot_model = ForgotPassword(email="demo@tnsr.ai")
    with patch("routers.auth.forgot_password_task") as mock_forgot_password_task, patch(
        "os.getenv", return_value="https://example.com"
    ) as mock_getenv:
        mock_forgot_password_task.return_value = {
            "detail": "Failed",
            "data": f"Email sent to demo@tnsr.ai",
        }
        response = client.post("/auth/forgotpassword", json=forgot_model.dict())
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["detail"] == "Failed"
        assert response.json()["data"] == "Email not found"


def test_verify_email_success(client, test_user):
    with patch("routers.auth.verify_email_task") as mock_verify_email_task:
        mock_verify_email_task.return_value = {
            "detail": "Success",
            "data": "Email verified successfully",
        }
        response = client.get("/auth/verifyemail?user_id=1&email_token=12345")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["detail"] == "Success"
        assert response.json()["data"] == "Email verified successfully"


def test_verify_email_failed(client, test_user):
    with patch("routers.auth.verify_email_task") as mock_verify_email_task:
        mock_verify_email_task.return_value = {
            "detail": "Failed",
            "data": "Email not verified",
        }
        response = client.get("/auth/verifyemail?user_id=1&email_token=12345")
        assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE
        assert response.json()["detail"] == "Email not verified"
