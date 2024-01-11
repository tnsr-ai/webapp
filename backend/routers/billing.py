import sys
from fastapi.responses import FileResponse, JSONResponse

sys.path.append("..")

from typing import Optional
from fastapi import Depends, HTTPException, APIRouter, BackgroundTasks, status, Request
import models
from database import engine, SessionLocal
from sqlalchemy import or_
from sqlalchemy.orm import Session
from pydantic import BaseModel
import time
from celeryworker import celeryapp
from routers.auth import get_current_user, TokenData
import json
import os
import requests
import pystache
from pathlib import Path
from pyhtml2pdf import converter
from fastapi_limiter.depends import RateLimiter
import stripe
from utils import TNSR_DOMAIN, STRIPE_SECRET_KEY, OPENEXCHANGERATES_API_KEY
from utils import (
    sql_dict,
    paymentinitiated_email,
    paymentsuccessfull_email,
    paymentfailed_email,
    increase_and_round,
)


router = APIRouter(
    prefix="/billing", tags=["billing"], responses={404: {"description": "Not found"}}
)

models.Base.metadata.create_all(bind=engine)

stripe.api_key = STRIPE_SECRET_KEY

with open("script_utils/symbol.json") as f:
    symbols = json.load(f)


class CheckoutModel(BaseModel):
    token: int
    currency_code: str


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


def billing_task(id: int, db: Session):
    try:
        user = db.query(models.Balance).filter(models.Balance.user_id == id).first()
        user_details = db.query(models.Users).filter(models.Users.id == id).first()
        if not user:
            create_balance_model = models.Balance(
                user_id=id, balance=0.0, lifetime_usage=0.0, created_at=int(time.time())
            )
            db.add(create_balance_model)
            db.commit()
            db.refresh(create_balance_model)
            data = sql_dict(create_balance_model)
            data["name"] = user_details.first_name
            return {
                "detail": "Success",
                "data": data,
                "verified": user_details.verified,
            }
        data = sql_dict(user)
        remove_keys = ["created_at", "updated_at"]
        for key in remove_keys:
            data.pop(key, None)
        data["tier"] = user_details.user_tier.capitalize()
        return {"detail": "Success", "data": data, "verified": user_details.verified}
    except Exception as e:
        return {"detail": "Failed", "data": str(e)}


@router.get(
    "/get_balance",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(times=10, seconds=60))],
)
async def get_stats(
    current_user: TokenData = Depends(get_current_user), db: Session = Depends(get_db)
):
    result = billing_task(current_user.user_id, db)
    if result["detail"] == "Success":
        return result
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=result["data"]
        )


def pricing_task(country_code: str, db: Session):
    try:
        with open("script_utils/currency.json") as f:
            data = json.load(f)
        if country_code not in data:
            country_code = "US"
        user_currency = data[country_code]
        accepted_currency = ["USD", "EUR", "GBP", "CAD", "AUD", "INR"]
        if user_currency not in accepted_currency:
            user_currency = "USD"
        currency_db = (
            db.query(models.Currency)
            .filter(models.Currency.name == user_currency)
            .first()
        )
        if currency_db is None:
            with open("script_utils/symbol.json") as f:
                symbols = json.load(f)
            exchange_api = OPENEXCHANGERATES_API_KEY
            base = "USD"
            url = f"https://openexchangerates.org/api/latest.json?app_id={exchange_api}&base={base}"
            response = requests.get(url)
            create_currency_model = models.Currency(
                name=user_currency,
                symbol=symbols[user_currency],
                rate=response.json()["rates"][user_currency],
                created_at=int(time.time()),
                updated_at=int(time.time()),
            )
            db.add(create_currency_model)
            db.commit()
            db.refresh(create_currency_model)
            return {
                "detail": "Success",
                "data": {
                    "currency": user_currency,
                    "symbol": symbols[user_currency],
                    "rate": create_currency_model.rate,
                },
            }
        if int(time.time()) - currency_db.updated_at > 604800:
            exchange_api = OPENEXCHANGERATES_API_KEY
            base = "USD"
            url = f"https://openexchangerates.org/api/latest.json?app_id={exchange_api}&base={base}"
            response = requests.get(url)
            currency_db.rate = response.json()["rates"][user_currency]
            currency_db.updated_at = int(time.time())
            db.commit()
            db.refresh(currency_db)
        return {
            "detail": "Success",
            "data": {
                "currency": user_currency,
                "symbol": currency_db.symbol,
                "rate": currency_db.rate,
                "country": country_code,
            },
        }
    except Exception as e:
        return {"detail": "Failed", "data": str(e)}


@router.get(
    "/price_conversion",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(times=10, seconds=60))],
)
async def price_conversion(
    countryCode: str,
    db: Session = Depends(get_db),
):
    result = pricing_task(countryCode, db)
    if result["detail"] == "Success":
        return result
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=result["data"]
        )


def checkout_task(user_id: int, token: int, currency_code: str, db: Session):
    try:
        user_data = db.query(models.Users).filter(models.Users.id == user_id).first()
        user_balance = (
            db.query(models.Balance).filter(models.Balance.user_id == user_id).first()
        )
        if user_balance is None:
            create_balance_model = models.Balance(
                user_id=user_id,
                balance=0.0,
                lifetime_usage=0.0,
                created_at=int(time.time()),
            )
            db.add(create_balance_model)
            db.commit()
            db.refresh(create_balance_model)
            user_balance = create_balance_model
        with open("script_utils/symbol.json") as f:
            data = json.load(f)
        currency_code = currency_code.upper()
        if currency_code not in data:
            currency_code = "USD"
        currency_db = (
            db.query(models.Currency)
            .filter(models.Currency.name == currency_code)
            .first()
        )
        if currency_db is None:
            return {"detail": "Failed", "data": "Currency not supported"}
        billing_amount = increase_and_round(int(token) * currency_db.rate, token)
        invoice_data = {
            "amount": billing_amount,
            "credits": token,
            "currency": currency_code,
            "symbol": currency_db.symbol,
        }
        create_invoice_model = models.Invoices(
            user_id=user_id,
            payment_gateway="stripe",
            data=json.dumps(invoice_data),
            amount=billing_amount["final_amt"],
            currency=currency_code,
            exchange_rate=currency_db.rate,
            status="pending",
            created_at=int(time.time()),
        )
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": currency_code,
                        "product_data": {
                            "name": f"{token} Credits",
                        },
                        "unit_amount": int(billing_amount["final_amt"] * 100),
                    },
                    "quantity": 1,
                },
            ],
            mode="payment",
            success_url=f"{TNSR_DOMAIN}/billing/?payment_status=success&token={token}",
            cancel_url=f"{TNSR_DOMAIN}/billing/?payment_status=failed&token={token}",
            customer_email=user_data.email,
        )
        create_invoice_model.session_id = checkout_session.id
        db.add(create_invoice_model)
        db.commit()
        db.refresh(create_invoice_model)
        return {
            "detail": "Success",
            "data": {"session_id": checkout_session.id},
            "amount": f"{invoice_data['symbol'].strip()}{billing_amount['final_amt']}",
        }
    except Exception as e:
        return {"detail": "Failed", "data": str(e)}


@celeryapp.task(name="routers.billing.send_paymentInitiated_email_task")
def send_paymentInitiated_email_task(
    user_id: int, payment_status: str, credits: int, amount: str
):
    db = SessionLocal()
    user_data = db.query(models.Users).filter(models.Users.id == user_id).first()
    if user_data is None:
        return {"detail": "Failed", "data": "User not found"}
    name = user_data.first_name
    receiver_email = user_data.email
    email_status = paymentinitiated_email(
        name, payment_status, credits, amount, receiver_email
    )
    db.close()
    if email_status == False:
        return {"detail": "Failed", "data": "Failed to send email"}
    return {"detail": "Success", "data": "Email sent successfully"}


@celeryapp.task(name="routers.billing.send_paymentSuccessfull_email_task")
def send_paymentSuccessfull_email_task(user_id: int, credits: int, amount: str):
    db = SessionLocal()
    user_data = db.query(models.Users).filter(models.Users.id == user_id).first()
    if user_data is None:
        return {"detail": "Failed", "data": "User not found"}
    name = user_data.first_name
    receiver_email = user_data.email
    email_status = paymentsuccessfull_email(name, credits, amount, receiver_email)
    db.close()
    if email_status == False:
        return {"detail": "Failed", "data": "Failed to send email"}
    return {"detail": "Success", "data": "Email sent successfully"}


@celeryapp.task(name="routers.billing.send_paymentFailed_email_task")
def send_paymentFailed_email_task(user_id: int, credits: int, amount: str):
    db = SessionLocal()
    user_data = db.query(models.Users).filter(models.Users.id == user_id).first()
    if user_data is None:
        return {"detail": "Failed", "data": "User not found"}
    name = user_data.first_name
    receiver_email = user_data.email
    email_status = paymentfailed_email(name, credits, amount, receiver_email)
    db.close()
    if email_status == False:
        return {"detail": "Failed", "data": "Failed to send email"}
    return {"detail": "Success", "data": "Email sent successfully"}


@router.post("/checkout", dependencies=[Depends(RateLimiter(times=5, seconds=60))])
async def create_checkout_session(
    checkout: CheckoutModel,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if checkout.token < 5:
        raise HTTPException(status_code=400, detail="Minimum token is 5")
    result = checkout_task(
        current_user.user_id, checkout.token, checkout.currency_code, db
    )
    if result["detail"] == "Success":
        send_paymentInitiated_email_task.delay(
            current_user.user_id, "Initiated", checkout.token, result["amount"]
        )
        return result
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=result["data"]
        )


def checkout_status_task(session_id: str, status: str, db: Session):
    try:
        invoice = (
            db.query(models.Invoices)
            .filter(models.Invoices.session_id == session_id)
            .first()
        )
        if invoice is None:
            return {"detail": "Failed", "data": "Invoice not found"}
        invoice_data = json.loads(invoice.data)
        if status == "success":
            invoice.status = "completed"
            session = stripe.checkout.Session.retrieve(session_id)
            payment_intent = stripe.PaymentIntent.retrieve(session.payment_intent)
            payment_method = stripe.PaymentMethod.retrieve(
                payment_intent.payment_method
            )
            invoice_data = json.loads(invoice.data)
            invoice_data["payment_card"] = payment_method.card.brand.lower()
            invoice_data["payment_card_last4"] = payment_method.card.last4
            invoice.data = json.dumps(invoice_data)
            user_balance = (
                db.query(models.Balance)
                .filter(models.Balance.user_id == invoice.user_id)
                .first()
            )
            user_balance.balance = user_balance.balance + int(invoice_data["credits"])
            user_balance.lifetime_usage = user_balance.lifetime_usage + int(
                invoice_data["credits"]
            )
            db.commit()
            db.refresh(user_balance)
            send_paymentSuccessfull_email_task.delay(
                invoice.user_id,
                invoice_data["credits"],
                f"{invoice_data['symbol'].strip()}{invoice_data['amount']['original']}",
            )
            return {"detail": "Success", "data": "Payment completed"}
        else:
            invoice.status = "failed"
            db.commit()
            send_paymentSuccessfull_email_task.delay(
                invoice.user_id,
                invoice_data["credits"],
                f"{invoice_data['symbol'].strip()}{invoice_data['amount']['original']}",
            )
            return {"detail": "Failed", "data": "Payment failed"}
    except Exception as e:
        return {"detail": "Failed", "data": str(e)}


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    event = None
    try:
        event = stripe.Event.construct_from(json.loads(payload), stripe.api_key)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid payload")
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        result = checkout_status_task(session.id, "success", db)
        if result["detail"] == "Success":
            return JSONResponse(
                status_code=200,
                content={"detail": "Success", "data": "Payment completed"},
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=result["data"]
            )
    elif event["type"] == "checkout.session.async_payment_failed":
        session = event["data"]["object"]
        result = checkout_status_task(session.id, "failed", db)
        if result["detail"] == "Success":
            return JSONResponse(
                status_code=200, content={"detail": "Success", "data": "Payment failed"}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=result["data"]
            )
    else:
        return JSONResponse(
            status_code=200, content={"detail": "Success", "data": "Payment failed"}
        )


def get_invoices_task(user_id: int, limit: int, offset: int, db: Session):
    try:
        invoices = (
            db.query(models.Invoices)
            .filter(models.Invoices.user_id == user_id)
            .filter(
                or_(
                    models.Invoices.status == "completed",
                    models.Invoices.status == "pending",
                )
            )
            .order_by(models.Invoices.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )
        all_invoices = (
            db.query(models.Invoices)
            .filter(models.Invoices.user_id == user_id)
            .filter(
                or_(
                    models.Invoices.status == "completed",
                    models.Invoices.status == "pending",
                )
            )
            .all()
        )
        if invoices is None:
            return {"detail": "Failed", "data": "Invoice not found"}
        total_invoices = len(all_invoices)
        data = []
        for invoice in invoices:
            invoice_data = sql_dict(invoice)
            invoice_data["data"] = json.loads(invoice_data["data"])
            month = time.strftime("%B", time.localtime(invoice_data["created_at"]))[:3]
            invoice_data["date"] = time.strftime(
                f"{month} %d,%Y,%H:%M", time.localtime(invoice_data["created_at"])
            )
            remove_keys = ["created_at", "updated_at"]
            for key in remove_keys:
                invoice_data.pop(key, None)
            payment_details = {}
            if invoice_data["status"] == "completed":
                payment_details["card"] = invoice_data["data"]["payment_card"]
                payment_details["last4"] = invoice_data["data"]["payment_card_last4"]
            else:
                payment_details["card"] = None
                payment_details["last4"] = None
            result = {
                "orderID": invoice_data["id"],
                "date": invoice_data["date"],
                "amount": invoice_data["amount"],
                "currency": symbols[invoice_data["currency"]],
                "status": invoice_data["status"].capitalize(),
                "payment_details": payment_details,
            }
            data.append(result)
        return {"detail": "Success", "data": data, "total": total_invoices}
    except Exception as e:
        return {"detail": "Failed", "data": str(e)}


@router.get(
    "/get_invoices",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
)
async def get_invoices(
    limit: int = 5,
    offset: int = 0,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if limit > 10:
        raise HTTPException(status_code=400, detail="Limit cannot be greater than 10")
    result = get_invoices_task(current_user.user_id, limit, offset, db)
    if result["detail"] == "Success":
        return result
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=result["data"]
        )


def download_invoice_task(user_id: int, invoice_id: int, db: Session):
    try:
        invoice_data = (
            db.query(models.Invoices)
            .filter(models.Invoices.user_id == user_id)
            .filter(models.Invoices.id == invoice_id)
            .first()
        )
        user_data = db.query(models.Users).filter(models.Users.id == user_id).first()
        if user_data is None:
            return {"detail": "Failed", "data": "User not found"}
        if invoice_data is None:
            return {"detail": "Failed", "data": "Invoice not found"}
        invoice_data = sql_dict(invoice_data)
        invoice_data["data"] = json.loads(invoice_data["data"])
        month = time.strftime("%B", time.localtime(invoice_data["created_at"]))[:3]
        invoice_data["date"] = time.strftime(
            f"{month} %d, %Y, %H:%M", time.localtime(invoice_data["created_at"])
        )
        email_template = (Path() / "invoice/index.html").read_text()
        tax_data = {}
        if invoice_data["currency"] == "INR":
            tax_data["tax"] = "GST (18%)"
            tax_data["percent"] = 0.18
            tax_data["product_price"] = float(invoice_data["amount"]) - (
                float(invoice_data["amount"]) * tax_data["percent"]
            )
            tax_data["product_price"] = round(tax_data["product_price"], 2)
            tax_data["price_tax"] = float(invoice_data["amount"]) * tax_data["percent"]
        else:
            tax_data["tax"] = "VAT (20%)"
            tax_data["percent"] = 0.20
            tax_data["product_price"] = float(invoice_data["amount"]) - (
                float(invoice_data["amount"]) * tax_data["percent"]
            )
            tax_data["product_price"] = round(tax_data["product_price"], 2)
            tax_data["price_tax"] = float(invoice_data["amount"]) * tax_data["percent"]

        template_params = {
            "invoice_no": "#" + str(int(invoice_data["id"]) + 1000),
            "date": invoice_data["date"],
            "gst": "ABCDEFG123",
            "name": user_data.first_name + " " + user_data.last_name,
            "email": user_data.email,
            "payment_method": invoice_data["payment_gateway"].capitalize(),
            "card": invoice_data["data"]["payment_card"],
            "last4_card": "** " + invoice_data["data"]["payment_card_last4"],
            "item": f"{invoice_data['data']['credits']} Credits",
            "price": f"{symbols[invoice_data['currency']]} {tax_data['product_price']}",
            "item_tax": tax_data["tax"],
            "price_tax": f"{symbols[invoice_data['currency']]} {tax_data['price_tax']}",
            "total": f"{symbols[invoice_data['currency']]} {invoice_data['amount']}",
        }
        final_email_html = pystache.render(email_template, template_params)
        with open(f"invoice/{invoice_id}.html", "w") as f:
            f.write(final_email_html)
        return {"detail": "Success", "data": f"{invoice_id}.html"}
    except Exception as e:
        return {"detail": "Failed", "data": str(e)}


def remove_file(path: str):
    if os.path.exists(path):
        os.remove(path)


@router.get(
    "/download_invoice",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
)
async def download_invoice(
    invoice_id: int,
    background_tasks: BackgroundTasks,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = download_invoice_task(current_user.user_id, invoice_id, db)
    if result["detail"] == "Success":
        path = os.path.abspath(f"invoice/{invoice_id}.html")
        converter.convert(f"file:///{path}", f"invoice/{invoice_id}.pdf", compress=True)
        background_tasks.add_task(remove_file, f"invoice/{invoice_id}.html")
        background_tasks.add_task(remove_file, f"invoice/{invoice_id}.pdf")
        return FileResponse(
            f"invoice/{invoice_id}.pdf",
            media_type="application/pdf",
            filename=f"{invoice_id}.pdf",
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=result["data"]
        )
