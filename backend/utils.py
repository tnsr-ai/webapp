import jwt
from dotenv import load_dotenv
from fastapi import HTTPException, status, Request
import os
from typing import Union, Any
from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
import boto3, botocore
from email.mime.image import MIMEImage
import pystache
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from token_throttler import TokenBucket, TokenThrottler
from token_throttler.storage import RuntimeStorage
import smtplib
import re
import ssl

load_dotenv()

CONTENT_EXPIRE = int(os.getenv("CONTENT_EXPIRE"))

# Cloudflare Credentials
CLOUDFLARE_ACCOUNT_ENDPOINT = os.getenv("CLOUDFLARE_ACCOUNT_ENDPOINT")
CLOUDFLARE_ACCESS_KEY = os.getenv("CLOUDFLARE_ACCESS_KEY")
CLOUDFLARE_SECRET_KEY = os.getenv("CLOUDFLARE_SECRET_KEY")
CLOUDFLARE_CONTENT = os.getenv("CLOUDFLARE_CONTENT")
CLOUDFLARE_METADATA = os.getenv("CLOUDFLARE_METADATA")
CLOUDFLARE_EXPIRE_TIME = os.getenv("CLOUDFLARE_EXPIRE_TIME")

# JWT Credentials
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_REFRESH_SECRET = os.getenv("JWT_REFRESH_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES"))
JWT_REFRESH_TOKEN_EXPIRE_MINUTES = eval(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_MINUTES"))
JWT_AUTH_TOKEN = os.getenv("JWT_AUTH_TOKEN")

# Google Credentials
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_SECRET_ID = os.getenv("GOOGLE_SECRET_ID")
GOOGLE_DISCOVERY_URL = os.getenv("GOOGLE_DISCOVERY_URL")
GOOGLE_SECRET = os.getenv("GOOGLE_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

# Website Credentials
TNSR_DOMAIN = os.getenv("TNSR_DOMAIN")
TNSR_BACKEND_DOMAIN = os.getenv("TNSR_BACKEND_DOMAIN")

# Redis Credentials
REDIS_BROKER = os.getenv("REDIS_BROKER")
REDIS_BACKEND = os.getenv("REDIS_BACKEND")
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")

# Grafana Credentials
LOKI_URL = os.getenv("LOKI_URL")
LOKI_USERNAME = os.getenv("LOKI_USERNAME")
LOKI_PASSWORD = os.getenv("LOKI_PASSWORD")

# Crypto Credentials
CRYPTO_TOKEN = os.getenv("CRYPTO_TOKEN")

# Email Credentials
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = os.getenv("SMTP_PORT")
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

# Stripe Credentials
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY")

# Openexchange Credentials
OPENEXCHANGERATES_API_KEY = os.getenv("OPENEXCHANGERATES_API_KEY")


STORAGE_LIMITS = {
    "free": 2 * 1024**3,  # 2GB
    "standard": 20 * 1024**3,  # 20GB
    "deluxe": 100 * 1024**3,  # 100GB
}

r2_client = boto3.client(
    "s3",
    aws_access_key_id=CLOUDFLARE_ACCESS_KEY,
    aws_secret_access_key=CLOUDFLARE_SECRET_KEY,
    endpoint_url=CLOUDFLARE_ACCOUNT_ENDPOINT,
    config=botocore.config.Config(
        s3={"addressing_style": "path"},
        signature_version="s3v4",
        retries=dict(max_attempts=3),
    ),
)

r2_resource = boto3.resource(
    "s3",
    aws_access_key_id=CLOUDFLARE_ACCESS_KEY,
    aws_secret_access_key=CLOUDFLARE_SECRET_KEY,
    endpoint_url=CLOUDFLARE_ACCOUNT_ENDPOINT,
)

throttler: TokenThrottler = TokenThrottler(cost=1, storage=RuntimeStorage())
throttler.add_bucket(
    identifier="user_id", bucket=TokenBucket(replenish_time=60, max_tokens=100)
)

throttler_checkout = TokenThrottler(cost=1, storage=RuntimeStorage())
throttler_checkout.add_bucket(
    identifier="user_id", bucket=TokenBucket(replenish_time=600, max_tokens=10)
)

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_hashed_password(password: str) -> str:
    return password_context.hash(password + JWT_AUTH_TOKEN)


def verify_password(password: str, hashed_pass: str) -> bool:
    return password_context.verify(password + JWT_AUTH_TOKEN, hashed_pass)


def isValidEmail(email: str) -> bool:
    pattern = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
    return re.match(pattern, email) is not None


def create_access_token(subject: Union[str, Any], expires_delta: int = None) -> str:
    if expires_delta is not None:
        expires_delta = datetime.utcnow() + expires_delta
    else:
        expires_delta = datetime.utcnow() + timedelta(
            minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expires_delta, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(subject: Union[str, Any], expires_delta: int = None) -> str:
    if expires_delta is not None:
        expires_delta = datetime.utcnow() + expires_delta
    else:
        expires_delta = datetime.utcnow() + timedelta(
            minutes=JWT_REFRESH_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expires_delta, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, JWT_REFRESH_SECRET, JWT_ALGORITHM)
    return encoded_jwt


def sql_dict(obj):
    result_dict = {x.name: getattr(obj, x.name) for x in obj.__table__.columns}
    return result_dict


def remove_key(data_list, key):
    for item in data_list:
        if key in item:
            del item[key]


def registration_email(name: str, verification: str, receiver_email: str):
    try:
        context = ssl.create_default_context()
        smtp_client = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context)
        smtp_client.login(SMTP_USERNAME, SMTP_PASSWORD)
        all_image_path = [
            Path() / "emailUtils/logo.png",
            Path() / "emailUtils/welcome.png",
            Path() / "emailUtils/twitter.png",
            Path() / "emailUtils/discord.png",
            Path() / "emailUtils/linkedin.png",
            Path() / "emailUtils/youtube.png",
        ]
        email_template = (Path() / "emailUtils/registration.html").read_text()
        template_params = {"name": name, "verification": verification}
        all_img = []
        for image_path in all_image_path:
            image = open(image_path, "rb")
            image_img = MIMEImage(image.read())
            image.close()
            image_img.add_header("Content-ID", f"<{image_path.name}>")
            image_img.add_header(
                "Content-Disposition", "inline", filename=image_path.name
            )
            template_params[image_path.stem] = image_path.name
            all_img.append(image_img)
        final_email_html = pystache.render(email_template, template_params)
        message = MIMEMultipart("related")
        message["Subject"] = "Email Verification"
        message["From"] = "welcome@tnsr.ai"
        message["To"] = receiver_email
        message.attach(MIMEText(final_email_html, "html"))
        for image in all_img:
            message.attach(image)
        smtp_client.sendmail("welcome@tnsr.ai", receiver_email, message.as_string())
        smtp_client.quit()
        return True
    except Exception as e:
        return str(e)


def forgotpassword_email(name: str, verification: str, receiver_email: str):
    try:
        context = ssl.create_default_context()
        smtp_client = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context)
        smtp_client.login(SMTP_USERNAME, SMTP_PASSWORD)
        all_image_path = [
            Path() / "emailUtils/logo.png",
            Path() / "emailUtils/forgot_password.png",
            Path() / "emailUtils/twitter.png",
            Path() / "emailUtils/discord.png",
            Path() / "emailUtils/linkedin.png",
            Path() / "emailUtils/youtube.png",
        ]
        email_template = (Path() / "emailUtils/forgot.html").read_text()
        template_params = {"name": name, "verification": verification}
        all_img = []
        for image_path in all_image_path:
            image = open(image_path, "rb")
            image_img = MIMEImage(image.read())
            image.close()
            image_img.add_header("Content-ID", f"<{image_path.name}>")
            image_img.add_header(
                "Content-Disposition", "inline", filename=image_path.name
            )
            template_params[image_path.stem] = image_path.name
            all_img.append(image_img)
        final_email_html = pystache.render(email_template, template_params)
        message = MIMEMultipart("related")
        message["Subject"] = "Reset Password"
        message["From"] = "support@tnsr.ai"
        message["To"] = receiver_email
        message.attach(MIMEText(final_email_html, "html"))
        for image in all_img:
            message.attach(image)
        smtp_client.sendmail("support@tnsr.ai", receiver_email, message.as_string())
        smtp_client.quit()
        return True
    except Exception as e:
        return False


def paymentinitiated_email(
    name: str, payment_status: str, credits: int, amount: str, receiver_email: str
):
    try:
        context = ssl.create_default_context()
        smtp_client = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context)
        smtp_client.login(SMTP_USERNAME, SMTP_PASSWORD)
        all_image_path = [
            Path() / "emailUtils/logo.png",
            Path() / "emailUtils/payment_initiated.png",
            Path() / "emailUtils/twitter.png",
            Path() / "emailUtils/discord.png",
            Path() / "emailUtils/linkedin.png",
            Path() / "emailUtils/youtube.png",
        ]
        email_template = (Path() / "emailUtils/payment_initiated.html").read_text()
        template_params = {
            "name": name,
            "payment_status": payment_status,
            "credits": credits,
            "amount": amount,
        }
        all_img = []
        for image_path in all_image_path:
            image = open(image_path, "rb")
            image_img = MIMEImage(image.read())
            image.close()
            image_img.add_header("Content-ID", f"<{image_path.name}>")
            image_img.add_header(
                "Content-Disposition", "inline", filename=image_path.name
            )
            template_params[image_path.stem] = image_path.name
            all_img.append(image_img)
        final_email_html = pystache.render(email_template, template_params)
        message = MIMEMultipart("related")
        message["Subject"] = f"Payment Initiated for {amount}"
        message["From"] = "billing@tnsr.ai"
        message["To"] = receiver_email
        message.attach(MIMEText(final_email_html, "html"))
        for image in all_img:
            message.attach(image)
        smtp_client.sendmail("billing@tnsr.ai", receiver_email, message.as_string())
        smtp_client.quit()
        return True
    except Exception as e:
        return False


def paymentsuccessfull_email(name: str, credits: int, amount: str, receiver_email: str):
    try:
        context = ssl.create_default_context()
        smtp_client = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context)
        smtp_client.login(SMTP_USERNAME, SMTP_PASSWORD)
        all_image_path = [
            Path() / "emailUtils/logo.png",
            Path() / "emailUtils/payment_successfull.png",
            Path() / "emailUtils/twitter.png",
            Path() / "emailUtils/discord.png",
            Path() / "emailUtils/linkedin.png",
            Path() / "emailUtils/youtube.png",
        ]
        email_template = (Path() / "emailUtils/payment_successfull.html").read_text()
        template_params = {"name": name, "credits": credits, "amount": amount}
        all_img = []
        for image_path in all_image_path:
            image = open(image_path, "rb")
            image_img = MIMEImage(image.read())
            image.close()
            image_img.add_header("Content-ID", f"<{image_path.name}>")
            image_img.add_header(
                "Content-Disposition", "inline", filename=image_path.name
            )
            template_params[image_path.stem] = image_path.name
            all_img.append(image_img)
        final_email_html = pystache.render(email_template, template_params)
        message = MIMEMultipart("related")
        message["Subject"] = f"Payment Successfull for {amount}"
        message["From"] = "billing@tnsr.ai"
        message["To"] = receiver_email
        message.attach(MIMEText(final_email_html, "html"))
        for image in all_img:
            message.attach(image)
        smtp_client.sendmail("billing@tnsr.ai", receiver_email, message.as_string())
        smtp_client.quit()
        return True
    except Exception as e:
        print(e)
        return False


def paymentfailed_email(name: str, credits: int, amount: str, receiver_email: str):
    try:
        context = ssl.create_default_context()
        smtp_client = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context)
        smtp_client.login(SMTP_USERNAME, SMTP_PASSWORD)
        all_image_path = [
            Path() / "emailUtils/logo.png",
            Path() / "emailUtils/payment_failed.png",
            Path() / "emailUtils/twitter.png",
            Path() / "emailUtils/discord.png",
            Path() / "emailUtils/linkedin.png",
            Path() / "emailUtils/youtube.png",
        ]
        email_template = (Path() / "emailUtils/payment_failed.html").read_text()
        template_params = {"name": name, "credits": credits, "amount": amount}
        all_img = []
        for image_path in all_image_path:
            image = open(image_path, "rb")
            image_img = MIMEImage(image.read())
            image.close()
            image_img.add_header("Content-ID", f"<{image_path.name}>")
            image_img.add_header(
                "Content-Disposition", "inline", filename=image_path.name
            )
            template_params[image_path.stem] = image_path.name
            all_img.append(image_img)
        final_email_html = pystache.render(email_template, template_params)
        message = MIMEMultipart("related")
        message["Subject"] = f"Payment Failed for {amount}"
        message["From"] = "billing@tnsr.ai"
        message["To"] = receiver_email
        message.attach(MIMEText(final_email_html, "html"))
        for image in all_img:
            message.attach(image)
        smtp_client.sendmail("billing@tnsr.ai", receiver_email, message.as_string())
        smtp_client.quit()
        return True
    except Exception as e:
        return False


def increase_and_round(number_val: int, credits: int) -> dict:
    if number_val == 0:
        return {"original": 0, "discounted": 0, "percentage": 0, "final_amt": 0}

    rounded_no = round(number_val)

    if rounded_no == 0:
        return {"original": 1, "discounted": 0, "percentage": 0, "final_amt": 1}

    discount = 0
    if 50 <= credits < 100:
        discount = 0.05  # 5% discount
    elif 100 <= credits < 200:
        discount = 0.1  # 10% discount
    elif 200 <= credits < 300:
        discount = 0.15  # 15% discount
    elif 300 <= credits < 400:
        discount = 0.2  # 20% discount
    elif 400 <= credits <= 500:
        discount = 0.25  # 25% discount

    if discount == 0:
        return {
            "original": rounded_no,
            "discounted": 0,
            "percentage": 0,
            "final_amt": rounded_no,
        }

    return {
        "original": rounded_no,
        "discounted": round(rounded_no * (1 - discount)),
        "percentage": discount * 100,
        "final_amt": round(rounded_no * (1 - discount)),
    }
