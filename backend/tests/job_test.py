from main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_fetch_routes():
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
