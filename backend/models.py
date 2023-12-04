from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, Enum, Float, BigInteger
from sqlalchemy.orm import relationship
from database import Base


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    user_tier = Column(Enum('free', 'standard', 'deluxe', name='user_tier', default='free'))
    verified = Column(Boolean, default=False)
    google_login = Column(Boolean, default=False)
    refreshVersion = Column(Integer, default=1)
    accessVersion = Column(Integer, default=1)
    email_token = Column(String, nullable=True)
    forgotpassword_token = Column(String, nullable=True)
    created_at = Column(Integer, nullable=True)
    updated_at = Column(Integer, nullable=True)

    videos = relationship("Videos", back_populates="user")
    audios = relationship("Audios", back_populates="user")
    images = relationship("Images", back_populates="user")
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

class Videos(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    link = Column(String)
    duration = Column(String)
    size = Column(String)
    fps = Column(String)
    resolution = Column(String)
    thumbnail = Column(String)
    tags = Column(String)
    md5 = Column(String)
    id_related = Column(Integer, nullable=True)
    created_at = Column(Integer, nullable=True)
    updated_at = Column(Integer, nullable=True)
    status = Column(Enum('pending', 'completed', 'failed', name='status'))
    
    user = relationship("Users", back_populates="videos")

class Audios(Base):
    __tablename__ = "audios"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    link = Column(String)
    duration = Column(String)
    size = Column(String)
    hz = Column(String)
    thumbnail = Column(String)
    tags = Column(String)
    md5 = Column(String)
    id_related = Column(Integer, nullable=True)
    created_at = Column(Integer, nullable=True)
    updated_at = Column(Integer, nullable=True)
    status = Column(Enum('pending', 'completed', 'failed', name='status'))
    
    user = relationship("Users", back_populates="audios")

class Images(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    link = Column(String)
    size = Column(String)
    thumbnail = Column(String)
    resolution = Column(String)
    tags = Column(String)
    md5 = Column(String)
    id_related = Column(Integer, nullable=True)
    created_at = Column(Integer, nullable=True)
    updated_at = Column(Integer, nullable=True)
    status = Column(Enum('pending', 'completed', 'failed', name='status'))

    user = relationship("Users", back_populates="images")

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
    status = Column(Enum('pending', 'completed', 'failed', name='invoice_status'))
    created_at = Column(Integer, nullable=True)
    updated_at = Column(Integer, nullable=True)

    user = relationship("Users", back_populates="invoices")

class Machines(Base):
    __tablename__ = "machines"

    machine_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    machine_ip = Column(String)
    machine_config = Column(String)
    machine_status = Column(Enum('available', 'busy', 'offline', name='machine_status'))
    job_id = Column(Integer, ForeignKey("jobs.job_id"))
    provider = Column(String)
    created_at = Column(Integer, nullable=True)
    updated_at = Column(Integer, nullable=True)

    user = relationship("Users", back_populates="machine")

class Jobs(Base):
    __tablename__ = "jobs"

    job_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
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
