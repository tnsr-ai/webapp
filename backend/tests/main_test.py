from main import app
from fastapi.testclient import TestClient
import pytest


@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client


def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "Server is running"}
