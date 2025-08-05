from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.mysql import LONGTEXT, VARCHAR, BOOLEAN, BIGINT, TEXT
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import LargeBinary, ForeignKey, String, Column, TIMESTAMP

from src.database import engine
from src.config import config

# Base class for declarative models
Base = declarative_base()


# Users table definition
class User(Base):
    __tablename__ = "users"

    id = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    last_login = Column(TIMESTAMP, nullable=False, server_default=func.now())
    username = Column(String(20), nullable=False)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    password = Column(String(255), nullable=False)
    remember_token = Column(VARCHAR(100), nullable=True)
    enabled = Column(BOOLEAN(), nullable=False, default=True)
    is_admin = Column(BOOLEAN(), nullable=False, default=False)


# Variables table definition
class Variable(Base):
    __tablename__ = "variables"

    id = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    key = Column(String(255), unique=True, nullable=False)
    value = Column(TEXT, nullable=True)
    type = Column(String(50), nullable=True)  # e.g. "int", "float", "bool", "str", "json"
    description = Column(String(1000), nullable=True)
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# Forms table definition
class Form(Base):
    __tablename__ = "forms"

    id = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    created_by = Column(BIGINT(unsigned=True), ForeignKey("users.id"), nullable=False)
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_by = Column(BIGINT(unsigned=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False, unique=True)
    content = Column(LONGTEXT, nullable=True)

    # Add two separate relationships, one for each FK
    creator = relationship("User", foreign_keys=[created_by], backref="created_forms")
    updater = relationship("User", foreign_keys=[updated_by], backref="updated_forms")

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# Guests Book table definition
class GuestBook(Base):
    __tablename__ = "guest_book"

    id = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=False)
    email = Column(String(255), nullable=True)
    pdf_file = Column(LargeBinary, nullable=False)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


def create_all_tables():
    Base.metadata.create_all(engine)


def drop_all_tables():
    Base.metadata.drop_all(engine)


def create_default_admin_user(session, username="admin", password=config.DATABASE_DEFAULT_PASSWORD):
    """
    Creates a default admin user if it does not exist.
    """
    from sqlalchemy import select

    from src.auth.__init__ import hash_password

    # Check if the admin user already exists
    existing = session.execute(select(User).where(User.username == username)).scalar_one_or_none()
    if existing:
        return False  # Admin user already exists

    admin_user = User(
        username=username,
        first_name="Admin",
        last_name="User",
        email="admin@example.com",
        password=hash_password(password),
        enabled=True,
        is_admin=True,
    )
    session.add(admin_user)
    session.commit()
    return True
