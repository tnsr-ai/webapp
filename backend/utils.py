import jwt
from dotenv import load_dotenv
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
import smtplib
import re
import ssl
import time
from typing import Tuple
import logging as logger
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import REGISTRY, Counter, Gauge, Histogram
from prometheus_client.openmetrics.exposition import (
    CONTENT_TYPE_LATEST,
    generate_latest,
)
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Match
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR
from starlette.types import ASGIApp

load_dotenv()
APP_ENV = os.getenv("APP_ENV")
if APP_ENV == "development":
    load_dotenv(dotenv_path=".env.development")
elif APP_ENV == "github":
    load_dotenv(dotenv_path=".env.github")
elif APP_ENV == "docker":
    load_dotenv(dotenv_path=".env.docker")
else:
    load_dotenv(dotenv_path=".env")

ENV = os.getenv("ENV")

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

# Database Credentials
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_USERNAME = os.getenv("POSTGRES_USERNAME")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DATABASE = os.getenv("POSTGRES_DATABASE")

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

# FastAPI Config
HOST = os.getenv("HOST")
PORT = os.getenv("PORT")


STORAGE_LIMITS = {
    "free": 2 * 1024**3,
    "standard": 20 * 1024**3,
    "deluxe": 100 * 1024**3,
}

INFO = Gauge("fastapi_app_info", "FastAPI application information.", ["app_name"])
REQUESTS = Counter(
    "fastapi_requests_total",
    "Total count of requests by method and path.",
    ["method", "path", "app_name"],
)
RESPONSES = Counter(
    "fastapi_responses_total",
    "Total count of responses by method, path and status codes.",
    ["method", "path", "status_code", "app_name"],
)
REQUESTS_PROCESSING_TIME = Histogram(
    "fastapi_requests_duration_seconds",
    "Histogram of requests processing time by path (in seconds)",
    ["method", "path", "app_name"],
)
EXCEPTIONS = Counter(
    "fastapi_exceptions_total",
    "Total count of exceptions raised by path and exception type",
    ["method", "path", "exception_type", "app_name"],
)
REQUESTS_IN_PROGRESS = Gauge(
    "fastapi_requests_in_progress",
    "Gauge of requests by method and path currently being processed",
    ["method", "path", "app_name"],
)

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
        discount = 0.05
    elif 100 <= credits < 200:
        discount = 0.1
    elif 200 <= credits < 300:
        discount = 0.15
    elif 300 <= credits < 400:
        discount = 0.2
    elif 400 <= credits <= 500:
        discount = 0.25

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


class PrometheusMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, app_name: str = "fastapi-app") -> None:
        super().__init__(app)
        self.app_name = app_name
        INFO.labels(app_name=self.app_name).inc()

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        method = request.method
        path, is_handled_path = self.get_path(request)

        if not is_handled_path:
            return await call_next(request)

        REQUESTS_IN_PROGRESS.labels(
            method=method, path=path, app_name=self.app_name
        ).inc()
        REQUESTS.labels(method=method, path=path, app_name=self.app_name).inc()
        before_time = time.perf_counter()
        try:
            response = await call_next(request)
        except BaseException as e:
            status_code = HTTP_500_INTERNAL_SERVER_ERROR
            EXCEPTIONS.labels(
                method=method,
                path=path,
                exception_type=type(e).__name__,
                app_name=self.app_name,
            ).inc()
            raise e from None
        else:
            status_code = response.status_code
            after_time = time.perf_counter()
            # retrieve trace id for exemplar
            span = trace.get_current_span()
            trace_id = trace.format_trace_id(span.get_span_context().trace_id)

            REQUESTS_PROCESSING_TIME.labels(
                method=method, path=path, app_name=self.app_name
            ).observe(after_time - before_time, exemplar={"TraceID": trace_id})
        finally:
            RESPONSES.labels(
                method=method,
                path=path,
                status_code=status_code,
                app_name=self.app_name,
            ).inc()
            REQUESTS_IN_PROGRESS.labels(
                method=method, path=path, app_name=self.app_name
            ).dec()

        return response

    @staticmethod
    def get_path(request: Request) -> Tuple[str, bool]:
        for route in request.app.routes:
            match, child_scope = route.matches(request.scope)
            if match == Match.FULL:
                return route.path, True

        return request.url.path, False


def metrics(request: Request) -> Response:
    return Response(
        generate_latest(REGISTRY), headers={"Content-Type": CONTENT_TYPE_LATEST}
    )


def setting_otlp(
    app: ASGIApp, app_name: str, endpoint: str, log_correlation: bool = True
) -> None:
    resource = Resource.create(
        attributes={"service.name": app_name, "compose_service": app_name}
    )
    tracer = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer)

    tracer.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))

    if log_correlation:
        LoggingInstrumentor().instrument(set_logging_format=True)

    FastAPIInstrumentor.instrument_app(app, tracer_provider=tracer)


def hide_email(email):
    local_part, domain = email.split("@")
    mask_length = len(local_part) - 2 if len(local_part) > 2 else len(local_part)
    show_length = (len(local_part) - mask_length) // 2
    if show_length > 0:
        masked_local = (
            local_part[:show_length] + "*" * mask_length + local_part[-show_length:]
        )
    else:
        masked_local = "*" * mask_length
    masked_email = masked_local + "@" + domain
    return masked_email


class EndpointFilter(logger.Filter):
    def filter(self, record: logger.LogRecord) -> bool:
        return record.getMessage().find("GET /metrics") == -1


logger.getLogger("uvicorn.access").addFilter(EndpointFilter())
