# Usage: locust -f locustfile.py --headless --users 10 --spawn-rate 1 -H http://0.0.0.0:8000
from locust import HttpUser, task, between


class QuickstartUser(HttpUser):
    wait_time = between(1, 2)

    @task(10)
    def io_task(self):
        headers = {
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MDUzNzg0NjMsInN1YiI6InsnaWQnOiAxLCAncmVmcmVzaFZlcnNpb24nOiAzMSwgJ2FjY2Vzc1ZlcnNpb24nOiA5OH0ifQ.aorIZ4ESnEKVd-n1Sfu9Npi8mzjkwesGLdb6E0LdiKU",
            "accept": "application/json",
        }
        self.client.get(
            "/dashboard/get_stats", name="/dashboard/get_stats", headers=headers
        )
