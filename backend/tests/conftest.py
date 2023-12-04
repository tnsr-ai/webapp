import sys
from pathlib import Path

root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from main import app
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
)
import pytest
from routers.auth import TokenData
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from fakeredis import FakeStrictRedis
import models

# Create an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


@pytest.fixture(scope="function")
def test_db_session():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Dependency override for the database session
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Dependency override for the Redis server
def override_get_redis():
    return FakeStrictRedis()


def override_get_current_user():
    return MagicMock(
        return_value=TokenData(user_id=1, refreshVersion=1, accessVersion=1)
    )


def override_get_current_user_refresh():
    return MagicMock(
        return_value=TokenData(user_id=1, refreshVersion=1, accessVersion=1)
    )


# Apply the dependency overrides
# Auth
app.dependency_overrides[auth.get_db] = override_get_db
app.dependency_overrides[auth.get_current_user] = override_get_current_user
app.dependency_overrides[
    auth.get_current_user_refresh
] = override_get_current_user_refresh
app.dependency_overrides[auth.get_redis] = override_get_redis

# Dashboard
app.dependency_overrides[dashboard.get_db] = override_get_db
app.dependency_overrides[dashboard.get_current_user] = override_get_current_user

# Upload
app.dependency_overrides[upload.get_db] = override_get_db
app.dependency_overrides[upload.get_current_user] = override_get_current_user

# Content
app.dependency_overrides[content.get_db] = override_get_db
app.dependency_overrides[content.get_current_user] = override_get_current_user
app.dependency_overrides[content.get_redis] = override_get_redis

# Settings
app.dependency_overrides[settings.get_db] = override_get_db
app.dependency_overrides[settings.get_current_user] = override_get_current_user

# Billing
app.dependency_overrides[billing.get_db] = override_get_db
app.dependency_overrides[billing.get_current_user] = override_get_current_user


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module", autouse=True)
def create_test_db():
    models.Base.metadata.create_all(bind=engine)
    yield
    models.Base.metadata.drop_all(bind=engine)
