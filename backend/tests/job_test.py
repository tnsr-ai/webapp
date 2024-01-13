from main import app
from fastapi.testclient import TestClient
import pytest


@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client


def test_fetch_routes(client):
    response = client.get("/jobs/fetch_routes")
    assert response.status_code == 200
    assert response.json() == {
        "detail": "Success",
        "data": {
            "getjob": "/jobs/fetch_jobs",
            "registerjob": "/jobs/register_job",
            "presignedurl": "/upload/generate_presigned_post",
            "indexfile": "/upload/indexfile",
            "updatejob": "/jobs/update_job_status",
        },
    }
