from main import app
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from fastapi import status
from utils import *
from routers.billing import CheckoutModel

client = TestClient(app)


def test_get_balance_success(client, create_test_db):
    with patch("routers.billing.billing_task") as mock_billing_task:
        mock_billing_task.return_value = {
            "detail": "Success",
            "data": 0,
            "verified": True,
        }
        response = client.get("/billing/get_balance")
        assert response.status_code == status.HTTP_200_OK


def test_get_balance_task_error(client, create_test_db):
    with patch("routers.billing.billing_task") as mock_billing_task:
        mock_billing_task.return_value = {
            "detail": "Failed",
            "data": 0,
            "verified": False,
        }
        response = client.get("/billing/get_balance")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_price_conversion(client, create_test_db):
    with patch("routers.billing.pricing_task") as mock_pricing_task:
        mock_pricing_task.return_value = {
            "detail": "Success",
            "data": {
                "currency": "INR",
                "symbol": "₹",
                "rate": "85.90",
                "country": "IN",
            },
        }
        response = client.get("/billing/price_conversion?countryCode=IN")
        assert response.status_code == status.HTTP_200_OK


def test_checkout_success(client, create_test_db):
    with patch("routers.billing.checkout_task") as mock_checkout_task, patch(
        "routers.billing.send_paymentInitiated_email_task"
    ) as mock_send_paymentInitiated_email_task:
        mock_checkout_task.return_value = {
            "detail": "Success",
            "data": {"session_id": "1234"},
            "amount": "₹1000",
        }
        mock_send_paymentInitiated_email_task.return_value = {
            "detail": "Success",
            "data": "Email sent successfully",
        }
        response = client.post(
            "/billing/checkout",
            json=CheckoutModel(token=10, currency_code="INR").dict(),
        )
        assert response.status_code == status.HTTP_200_OK


def test_checkout_failed(client, create_test_db):
    with patch("routers.billing.checkout_task") as mock_checkout_task, patch(
        "routers.billing.send_paymentInitiated_email_task"
    ) as mock_send_paymentInitiated_email_task:
        mock_checkout_task.return_value = {
            "detail": "Failed",
            "data": {"session_id": "1234"},
            "amount": "₹1000",
        }
        mock_send_paymentInitiated_email_task.return_value = {
            "detail": "Failed",
            "data": "Email sent successfully",
        }
        response = client.post(
            "/billing/checkout",
            json=CheckoutModel(token=10, currency_code="INR").dict(),
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_get_invoices(client, create_test_db):
    with patch("routers.billing.get_invoices_task") as mock_get_invoices_task:
        mock_get_invoices_task.return_value = {
            "detail": "Success",
            "data": [
                {
                    "id": "1234",
                    "amount": "₹1000",
                    "currency": "INR",
                    "status": "paid",
                    "created_at": "2021-01-01 00:00:00",
                    "updated_at": "2021-01-01 00:00:00",
                }
            ],
        }
        response = client.get("/billing/get_invoices/?limit=5&offset=0")
        assert response.status_code == status.HTTP_200_OK


def test_get_invoices_failed(client, create_test_db):
    with patch("routers.billing.get_invoices_task") as mock_get_invoices_task:
        mock_get_invoices_task.return_value = {
            "detail": "Success",
            "data": [
                {
                    "id": "1234",
                    "amount": "₹1000",
                    "currency": "INR",
                    "status": "paid",
                    "created_at": "2021-01-01 00:00:00",
                    "updated_at": "2021-01-01 00:00:00",
                }
            ],
        }
        response = client.get("/billing/get_invoices/?limit=11&offset=0")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
