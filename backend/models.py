from sqlalchemy import (
    Boolean,
    Column,
    Integer,
    String,
    ForeignKey,
    Enum,
    Float,
    BigInteger,
)
from sqlalchemy.orm import relationship
from database import Base
import enum
import time


class ContentStatus(enum.Enum):
    def __str__(self):
        return str(self.value)

    processing = "processing"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"
    indexing = "indexing"


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    user_tier = Column(
        Enum(
            "free",
            "standard",
            "deluxe",
            name="user_tier_enum_" + str(int(time.time())),
            default="free",
            create_type=False,
        )
    )
    verified = Column(Boolean, default=False)
    google_login = Column(Boolean, default=False)
    refreshVersion = Column(Integer, default=1)
    accessVersion = Column(Integer, default=1)
    email_token = Column(String, nullable=True)
    forgotpassword_token = Column(String, nullable=True)
    created_at = Column(Integer, nullable=True)
    updated_at = Column(Integer, nullable=True)

    content = relationship("Content", back_populates="user")
    user_settings = relationship("UserSetting", back_populates="user")
    jobs = relationship("Jobs", back_populates="user")
    balance = relationship("Balance", back_populates="user")
    invoices = relationship("Invoices", back_populates="user")
    dashboard = relationship("Dashboard", back_populates="user")
    machine = relationship("Machines", back_populates="user")


class Dashboard(Base):
    __tablename__ = "dashboard"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True, index=True)
    video_processed = Column(Integer)
    audio_processed = Column(Integer)
    image_processed = Column(Integer)
    downloads = Column(BigInteger)
    uploads = Column(BigInteger)
    storage_used = Column(BigInteger)
    storage_limit = Column(BigInteger)
    gpu_usage = Column(BigInteger)
    storage_json = Column(String)
    created_at = Column(Integer, nullable=True)
    updated_at = Column(Integer, nullable=True)

    user = relationship("Users", back_populates="dashboard")


class Content(Base):
    __tablename__ = "content"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    link = Column(String)
    size = Column(String)
    thumbnail = Column(String)
    md5 = Column(String)
    created_at = Column(Integer, nullable=True)
    updated_at = Column(Integer, nullable=True)
    id_related = Column(Integer, nullable=True)
    job_id = Column(Integer, nullable=True)
    status = Column(Enum(ContentStatus, name="content_status_" + str(int(time.time())), create_type=False))
    content_type = Column(
        Enum("video", "audio", "image", "subtitle", "zip", name="content_type_" + str(int(time.time())), create_type=False)
    )
    duration = Column(String, nullable=True)
    resolution = Column(String, nullable=True)
    fps = Column(String, nullable=True)
    hz = Column(String, nullable=True)

    user = relationship("Users", back_populates="content")


class Balance(Base):
    __tablename__ = "balance"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True, index=True)
    balance = Column(Float)
    lifetime_usage = Column(Integer, default=0.0)
    created_at = Column(Integer, nullable=True)
    updated_at = Column(Integer, nullable=True)

    user = relationship("Users", back_populates="balance")


class Invoices(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    payment_gateway = Column(String)
    session_id = Column(String, nullable=True)
    data = Column(String)
    amount = Column(Float)
    currency = Column(String)
    exchange_rate = Column(Float)
    status = Column(
        Enum("pending", "completed", "failed", name="invoice_status_" + str(int(time.time())), create_type=False)
    )
    created_at = Column(Integer, nullable=True)
    updated_at = Column(Integer, nullable=True)

    user = relationship("Users", back_populates="invoices")


class Machines(Base):
    __tablename__ = "machines"

    machine_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    instance_id = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))
    machine_status = Column(
        Enum("LOADING", "RUNNING", "EXITED", "CANCELLED", "FAILED", name="machine_status_" + str(int(time.time())), create_type=False)
    )
    job_id = Column(Integer, ForeignKey("jobs.job_id"))
    provider = Column(String)
    created_at = Column(Integer, nullable=True)
    updated_at = Column(Integer, nullable=True)

    user = relationship("Users", back_populates="machine")


class Jobs(Base):
    __tablename__ = "jobs"

    job_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    celery_id = Column(String, nullable=True)
    content_id = Column(Integer, ForeignKey("content.id"))
    job_name = Column(String)
    job_type = Column(String)
    job_status = Column(String)
    job_tier = Column(String)
    created_at = Column(Integer, nullable=True)
    updated_at = Column(Integer, nullable=True)
    job_key = Column(Boolean, default=False)
    config_json = Column(String)
    job_process = Column(String)
    key = Column(String)

    user = relationship("Users", back_populates="jobs")
    content = relationship("Content")


class UserSetting(Base):
    __tablename__ = "user_settings"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True, index=True)
    newsletter = Column(Boolean, default=True)
    email_notification = Column(Boolean, default=True)
    discord_webhook = Column(String)
    created_at = Column(Integer, nullable=True)
    updated_at = Column(Integer, nullable=True)

    user = relationship("Users", back_populates="user_settings")


class Currency(Base):
    __tablename__ = "currency"

    name = Column(String, primary_key=True, index=True)
    symbol = Column(String)
    rate = Column(Integer)
    created_at = Column(Integer, nullable=True)
    updated_at = Column(Integer, nullable=True)


class Tags(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    tag = Column(String)
    readable = Column(String)
    created_at = Column(Integer, nullable=True)
    updated_at = Column(Integer, nullable=True)


class ContentTags(Base):
    __tablename__ = "content_tags"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    content_id = Column(Integer, ForeignKey("content.id"))
    tag_id = Column(Integer, ForeignKey("tags.id"))
    created_at = Column(Integer, nullable=True)
    updated_at = Column(Integer, nullable=True)

    content = relationship("Content")
    tags = relationship("Tags")
