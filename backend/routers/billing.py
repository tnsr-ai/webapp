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
from weasyprint import HTML, CSS
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
from utils import logger


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
        data["balance"] = round(data["balance"], 2)
        remove_keys = ["created_at", "updated_at"]
        for key in remove_keys:
            data.pop(key, None)
        data["tier"] = user_details.user_tier.capitalize()
        return {"detail": "Success", "data": data, "verified": user_details.verified}
    except Exception as e:
        return {"detail": "Failed", "data": str(e)}


def update_user_tier(user_id: int, db: Session):
    """
    Update user tier based on their lifetime spending.
    
    Args:
        user_id: The ID of the user to update
        db: Database session
        
    Returns:
        dict: Result with status and updated tier or error message
    """
    try:
        # Get user and balance information
        user = db.query(models.Users).filter(models.Users.id == user_id).first()
        if not user:
            return {"detail": "Failed", "data": "User not found"}
            
        balance = db.query(models.Balance).filter(models.Balance.user_id == user_id).first()
        if not balance:
            return {"detail": "Failed", "data": "Balance not found"}
        
        # Calculate total spending from all completed invoices
        total_spending = (
            db.query(models.Invoices)
            .filter(models.Invoices.user_id == user_id)
            .filter(models.Invoices.status == "completed")
            .with_entities(models.Invoices.amount)
            .all()
        )
        
        # Sum up all the amounts
        total_amount = sum(invoice.amount for invoice in total_spending)
        
        # Determine the new tier based on spending
        new_tier = "free"  # Default tier
        if total_amount > 100:
            new_tier = "deluxe"
        elif total_amount > 30:
            new_tier = "standard"
        
        # Update the user's tier if it has changed
        if user.user_tier != new_tier:
            user.user_tier = new_tier
            db.commit()
            db.refresh(user)
            logger.info(f"User {user_id} tier updated to {new_tier} (total spending: ${total_amount})")
            return {"detail": "Success", "data": {"tier": new_tier, "updated": True}}
        else:
            logger.info(f"User {user_id} tier remains {new_tier} (total spending: ${total_amount})")
            return {"detail": "Success", "data": {"tier": new_tier, "updated": False}}
            
    except Exception as e:
        logger.error(f"Failed to update user tier: {str(e)}")
        return {"detail": "Failed", "data": str(e)}


@router.get(
    "/get_balance",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(times=60, seconds=60))],
)
async def get_stats(
    current_user: TokenData = Depends(get_current_user), db: Session = Depends(get_db)
):
    result = billing_task(current_user.user_id, db)
    if result["detail"] == "Success":
        logger.info(f"User {current_user.user_id} get balance")
        return result
    else:
        logger.error(f"User {current_user.user_id} get balance failed")
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
    dependencies=[Depends(RateLimiter(times=60, seconds=60))],
)
async def price_conversion(
    countryCode: str,
    db: Session = Depends(get_db),
):
    result = pricing_task(countryCode, db)
    if result["detail"] == "Success":
        logger.info(f"User get price conversion")
        return result
    else:
        logger.error(f"User get price conversion failed")
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
            "id": create_invoice_model.id,
        }
    except Exception as e:
        return {"detail": "Failed", "data": str(e)}


@celeryapp.task(name="routers.billing.send_paymentInitiated_email_task", acks_late=True)
def send_paymentInitiated_email_task(
    user_id: int, payment_status: str, credits: int, amount: str, invoice_id: int
):
    with Session(engine) as db:
        user_data = db.query(models.Users).filter(models.Users.id == user_id).first()
        if user_data is None:
            return {"detail": "Failed", "data": "User not found"}
        name = user_data.first_name
        receiver_email = user_data.email
        email_status = paymentinitiated_email(
            name, payment_status, credits, amount, receiver_email, invoice_id
        )
        if email_status == False:
            return {"detail": "Failed", "data": "Failed to send email"}
        return {"detail": "Success", "data": "Email sent successfully"}


@celeryapp.task(
    name="routers.billing.send_paymentSuccessfull_email_task", acks_late=True
)
def send_paymentSuccessfull_email_task(user_id: int, credits: int, amount: str):
    with Session(engine) as db:
        user_data = db.query(models.Users).filter(models.Users.id == user_id).first()
        if user_data is None:
            return {"detail": "Failed", "data": "User not found"}
        name = user_data.first_name
        receiver_email = user_data.email
        email_status = paymentsuccessfull_email(name, credits, amount, receiver_email)
        if email_status == False:
            return {"detail": "Failed", "data": "Failed to send email"}
        return {"detail": "Success", "data": "Email sent successfully"}


@celeryapp.task(name="routers.billing.send_paymentFailed_email_task", acks_late=True)
def send_paymentFailed_email_task(user_id: int, credits: int, amount: str):
    with Session(engine) as db:
        user_data = db.query(models.Users).filter(models.Users.id == user_id).first()
        if user_data is None:
            return {"detail": "Failed", "data": "User not found"}
        name = user_data.first_name
        receiver_email = user_data.email
        email_status = paymentfailed_email(name, credits, amount, receiver_email)
        if email_status == False:
            return {"detail": "Failed", "data": "Failed to send email"}
        return {"detail": "Success", "data": "Email sent successfully"}


@router.post("/checkout", dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def create_checkout_session(
    checkout: CheckoutModel,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if checkout.token < 5:
        logger.error(
            f"User {current_user.user_id} checkout failed - Minimum token is 5"
        )
        raise HTTPException(status_code=400, detail="Minimum token is 5")
    result = checkout_task(
        current_user.user_id, checkout.token, checkout.currency_code, db
    )
    if result["detail"] == "Success":
        logger.info(f"User {current_user.user_id} checkout initiated")
        send_paymentInitiated_email_task.delay(
            current_user.user_id,
            "Initiated",
            checkout.token,
            result["amount"],
            result["id"],
        )
        return result
    else:
        logger.error(f"User {current_user.user_id} checkout failed")
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
            logger.error(f"Checkout status failed - Invoice not found")
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
            
            # Update user tier based on lifetime spending
            tier_update_result = update_user_tier(invoice.user_id, db)
            if tier_update_result["detail"] == "Success" and tier_update_result["data"]["updated"]:
                logger.info(f"User {invoice.user_id} tier updated to {tier_update_result['data']['tier']} after payment")
            
            send_paymentSuccessfull_email_task.delay(
                invoice.user_id,
                invoice_data["credits"],
                f"{invoice_data['symbol'].strip()}{invoice_data['amount']['original']}",
            )
            logger.info(f"Checkout status success - Payment completed")
            return {"detail": "Success", "data": "Payment completed"}
        else:
            invoice.status = "failed"
            db.commit()
            send_paymentSuccessfull_email_task.delay(
                invoice.user_id,
                invoice_data["credits"],
                f"{invoice_data['symbol'].strip()}{invoice_data['amount']['original']}",
            )
            logger.info(f"Checkout status success - Payment failed")
            return {"detail": "Failed", "data": "Payment failed"}
    except Exception as e:
        logger.error(f"Checkout status failed - {str(e)}")
        return {"detail": "Failed", "data": str(e)}


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    event = None
    try:
        event = stripe.Event.construct_from(json.loads(payload), stripe.api_key)
    except ValueError as e:
        logger.error(f"Invalid payload - {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        result = checkout_status_task(session.id, "success", db)
        if result["detail"] == "Success":
            logger.info(f"Checkout status success - Payment completed")
            return JSONResponse(
                status_code=200,
                content={"detail": "Success", "data": "Payment completed"},
            )
        else:
            logger.error(f"Checkout status failed - Payment failed")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=result["data"]
            )
    elif event["type"] == "checkout.session.async_payment_failed":
        session = event["data"]["object"]
        result = checkout_status_task(session.id, "failed", db)
        if result["detail"] == "Success":
            logger.info(f"Checkout status success - Payment failed")
            return JSONResponse(
                status_code=200, content={"detail": "Success", "data": "Payment failed"}
            )
        else:
            logger.error(f"Checkout status failed - Payment failed")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=result["data"]
            )
    else:
        logger.error(f"Checkout status failed - Payment failed")
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
            payment_details = {}
            if invoice_data["status"] == "completed":
                payment_details["card"] = invoice_data["data"]["payment_card"]
                payment_details["last4"] = invoice_data["data"]["payment_card_last4"]
            else:
                payment_details["card"] = None
                payment_details["last4"] = None
            result = {
                "orderID": invoice_data["id"],
                "date": invoice_data["created_at"],
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
    dependencies=[Depends(RateLimiter(times=60, seconds=60))],
)
async def get_invoices(
    limit: int = 5,
    offset: int = 0,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if limit > 10:
        logger.error(f"User {current_user.user_id} get invoices failed - Limit > 10")
        raise HTTPException(status_code=400, detail="Limit cannot be greater than 10")
    result = get_invoices_task(current_user.user_id, limit, offset, db)
    if result["detail"] == "Success":
        logger.info(f"User {current_user.user_id} get invoices")
        return result
    else:
        logger.error(f"User {current_user.user_id} get invoices failed")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=result["data"]
        )


def download_invoice_task(user_id: int, invoice_id: int, db: Session):
    """
    Generate an HTML invoice for a specific invoice ID.
    
    Args:
        user_id: The ID of the user requesting the invoice
        invoice_id: The ID of the invoice to generate
        db: Database session
        
    Returns:
        dict: Result with status and file path or error message
    """
    # Validate input parameters
    if not isinstance(user_id, int) or user_id <= 0:
        return {"detail": "Failed", "data": "Invalid user ID"}
    if not isinstance(invoice_id, int) or invoice_id <= 0:
        return {"detail": "Failed", "data": "Invalid invoice ID"}
    
    try:
        # Query invoice with proper error handling
        invoice = (
            db.query(models.Invoices)
            .filter(models.Invoices.user_id == user_id)
            .filter(models.Invoices.id == invoice_id)
            .first()
        )
        
        if invoice is None:
            logger.warning(f"Invoice {invoice_id} not found for user {user_id}")
            return {"detail": "Failed", "data": "Invoice not found"}
            
        # Query user data
        user = db.query(models.Users).filter(models.Users.id == user_id).first()
        if user is None:
            logger.error(f"User {user_id} not found")
            return {"detail": "Failed", "data": "User not found"}
        
        # Convert invoice to dictionary and parse JSON data
        try:
            invoice_dict = sql_dict(invoice)
            invoice_data = json.loads(invoice_dict["data"])
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Failed to parse invoice data: {str(e)}")
            return {"detail": "Failed", "data": "Invalid invoice data format"}
        
        # Validate required invoice data fields
        required_fields = ["credits", "amount"]
        for field in required_fields:
            if field not in invoice_data:
                logger.error(f"Missing required field in invoice data: {field}")
                return {"detail": "Failed", "data": f"Invoice data is incomplete: missing {field}"}
        
        # Format date
        try:
            month = time.strftime("%B", time.localtime(invoice_dict["created_at"]))[:3]
            formatted_date = time.strftime(
                f"{month} %d, %Y, %H:%M", time.localtime(invoice_dict["created_at"])
            )
        except (ValueError, TypeError) as e:
            logger.error(f"Failed to format invoice date: {str(e)}")
            formatted_date = "Unknown Date"
        
        # Load HTML template with error handling
        try:
            template_path = Path("invoice/index.html")
            if not template_path.exists():
                logger.error("Invoice template not found")
                return {"detail": "Failed", "data": "Invoice template not found"}
            email_template = template_path.read_text()
        except (IOError, OSError) as e:
            logger.error(f"Failed to read invoice template: {str(e)}")
            return {"detail": "Failed", "data": "Failed to load invoice template"}
        
        # Calculate tax based on currency
        try:
            currency = invoice_dict.get("currency", "USD")
            amount = float(invoice_dict["amount"])
            
            if currency == "INR":
                tax_data = {
                    "tax": "GST (18%)",
                    "percent": 0.18,
                    "product_price": round(amount / 1.18, 2),
                    "price_tax": round(amount - (amount / 1.18), 2)
                }
            else:
                tax_data = {
                    "tax": "VAT (20%)",
                    "percent": 0.20,
                    "product_price": round(amount / 1.20, 2),
                    "price_tax": round(amount - (amount / 1.20), 2)
                }
        except (ValueError, TypeError, ZeroDivisionError) as e:
            logger.error(f"Failed to calculate tax: {str(e)}")
            return {"detail": "Failed", "data": "Failed to calculate invoice amounts"}
        
        # Get currency symbol with fallback
        currency_symbol = symbols.get(currency, "$")
        
        # Prepare template parameters with validation
        try:
            # Handle payment card information safely
            payment_card = invoice_data.get("payment_card", "unknown")
            payment_card_last4 = invoice_data.get("payment_card_last4", "****")
            
            template_params = {
                "invoice_no": "#" + str(int(invoice_dict["id"]) + 1000),
                "date": formatted_date,
                "gst": "ABCDEFG123",
                "name": f"{user.first_name or ''} {user.last_name or ''}".strip() or "Valued Customer",
                "email": user.email or "",
                "payment_method": invoice_dict.get("payment_gateway", "Unknown").capitalize(),
                "card": payment_card,
                "last4_card": "** " + str(payment_card_last4),
                "item": f"{invoice_data.get('credits', 0)} Credits",
                "price": f"{currency_symbol} {tax_data['product_price']}",
                "item_tax": tax_data["tax"],
                "price_tax": f"{currency_symbol} {tax_data['price_tax']}",
                "total": f"{currency_symbol} {amount}",
            }
        except Exception as e:
            logger.error(f"Failed to prepare template parameters: {str(e)}")
            return {"detail": "Failed", "data": "Failed to prepare invoice data"}
        
        # Render HTML template
        try:
            final_html = pystache.render(email_template, template_params)
        except Exception as e:
            logger.error(f"Failed to render HTML template: {str(e)}")
            return {"detail": "Failed", "data": "Failed to generate invoice HTML"}
        
        # Write HTML file with proper path handling
        try:
            # Ensure invoice directory exists
            invoice_dir = Path("invoice")
            invoice_dir.mkdir(exist_ok=True)
            
            # Create a unique filename to avoid conflicts
            html_filename = f"invoice_{invoice_id}_{user_id}_{int(time.time())}.html"
            html_path = invoice_dir / html_filename
            
            # Write the file
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(final_html)
                
            logger.info(f"Successfully generated invoice HTML: {html_filename}")
            return {"detail": "Success", "data": html_filename}
            
        except (IOError, OSError) as e:
            logger.error(f"Failed to write invoice HTML file: {str(e)}")
            return {"detail": "Failed", "data": "Failed to save invoice file"}
            
    except Exception as e:
        logger.error(f"Unexpected error in download_invoice_task: {str(e)}")
        return {"detail": "Failed", "data": "An unexpected error occurred while generating the invoice"}


def remove_file(path: str):
    """
    Safely remove a file if it exists.
    
    Args:
        path: Path to the file to remove
    """
    try:
        file_path = Path(path)
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Successfully removed file: {path}")
        else:
            logger.warning(f"File not found for removal: {path}")
    except Exception as e:
        logger.error(f"Failed to remove file {path}: {str(e)}")


@router.get(
    "/download_invoice",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(times=10, seconds=60))],
)
async def download_invoice(
    invoice_id: int,
    background_tasks: BackgroundTasks,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Download an invoice as a PDF file.
    
    Args:
        invoice_id: The ID of the invoice to download
        background_tasks: FastAPI background tasks for cleanup
        current_user: The authenticated user
        db: Database session
        
    Returns:
        FileResponse: PDF file of the invoice
        
    Raises:
        HTTPException: If invoice generation fails
    """
    # Validate invoice_id parameter
    if not isinstance(invoice_id, int) or invoice_id <= 0:
        logger.error(f"User {current_user.user_id} provided invalid invoice_id: {invoice_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid invoice ID"
        )
    
    # Generate the HTML invoice
    result = download_invoice_task(current_user.user_id, invoice_id, db)
    
    if result["detail"] != "Success":
        logger.error(f"User {current_user.user_id} download invoice failed: {result['data']}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["data"]
        )
    
    html_filename = result["data"]
    html_path = Path("invoice") / html_filename
    
    # Verify the HTML file was created
    if not html_path.exists():
        logger.error(f"Generated HTML file not found: {html_path}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate invoice file"
        )
    
    # Generate PDF filename
    pdf_filename = html_filename.replace(".html", ".pdf")
    pdf_path = Path("invoice") / pdf_filename
    
    try:
        # Convert HTML to PDF with WeasyPrint
        logger.info(f"Converting HTML to PDF: {html_path} -> {pdf_path}")
        
        # Read the HTML content
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Add WeasyPrint-specific CSS to fix layout issues
        weasyprint_css = """
        @page {
            size: A4;
            margin: 2cm;
        }
        
        /* Fix card icon size */
        img[alt="card_logo"], .card-logo {
            width: 30px !important;
            height: 20px !important;
            max-width: 30px !important;
            max-height: 20px !important;
            object-fit: contain;
        }
        
        /* Fix table layout */
        .invoice-box table {
            width: 100%;
            line-height: inherit;
            text-align: left;
            border-collapse: collapse;
        }
        
        /* Fix details row alignment */
        .invoice-box table tr.details td:nth-child(2) {
            text-align: right !important;
        }
        
        /* Fix flex container in details */
        .invoice-box table tr.details td div {
            display: flex;
            justify-content: flex-end;
            align-items: center;
        }
        
        /* Fix image sizing in general */
        img {
            max-width: 100%;
            height: auto;
        }
        
        /* Ensure proper font rendering */
        body {
            font-family: 'Helvetica Neue', 'Helvetica', Helvetica, Arial, sans-serif;
            -weasy-print-mode: print;
        }
        """
        
        # Convert HTML to PDF using WeasyPrint
        html_doc = HTML(string=html_content, base_url=str(html_path.parent))
        
        # Generate PDF with proper styling for WeasyPrint
        html_doc.write_pdf(str(pdf_path), stylesheets=[CSS(string=weasyprint_css)])
        
        # Verify PDF was created
        if not pdf_path.exists():
            logger.error(f"PDF conversion failed: {pdf_path}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate PDF file"
            )
            
        logger.info(f"Successfully generated PDF: {pdf_path}")
        
        # Schedule cleanup of temporary files
        background_tasks.add_task(remove_file, str(html_path))
        background_tasks.add_task(remove_file, str(pdf_path))
        
        logger.info(f"User {current_user.user_id} successfully downloaded invoice {invoice_id}")
        
        # Return the PDF file
        return FileResponse(
            path=str(pdf_path),
            media_type="application/pdf",
            filename=f"invoice_{invoice_id}.pdf",
        )
        
    except Exception as e:
        logger.error(f"Error during PDF conversion for invoice {invoice_id}: {str(e)}")
        
        # Clean up HTML file if PDF conversion failed
        if html_path.exists():
            remove_file(str(html_path))
            
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate invoice PDF"
        )
