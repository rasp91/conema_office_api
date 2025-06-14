import datetime
from typing import Optional

import pytz
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from fastapi import status, HTTPException, APIRouter, Depends, Header
from jose import jwt, JWTError

from src.database.models import User
from src.auth.schemas import *
from src.database import get_db
from src.config import config

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
optional_oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

# Router
router = APIRouter()


def format_username(username: str) -> str:
    return username.strip().lower()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_user(db: Session, username: str) -> User | None:
    user = db.execute(select(User).where(and_(User.username == username, User.enabled == 1))).scalar_one_or_none()
    if user:
        return user
    return None


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    user = get_user(db, username)
    if not user or not verify_password(password, user.password):
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None):
    to_encode = data.copy()
    expire = datetime.datetime.now(pytz.utc) + (expires_delta if expires_delta else datetime.timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)


async def get_auth_user(token: str = Depends(oauth2_scheme)) -> AuthUser:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=config.JWT_ALGORITHM)
        username: str = payload.get("username")
        exp: int = payload.get("exp")
        if username is None or exp is None:
            raise credentials_exception
        # Check if token is expired
        if datetime.datetime.fromtimestamp(exp, pytz.utc) < datetime.datetime.now(pytz.utc):
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return AuthUser(**payload)


async def get_admin_user(token: str = Depends(oauth2_scheme)) -> AuthUser:
    user = await get_auth_user(token)
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return user


async def get_optional_auth_user(token: Optional[str] = Depends(optional_oauth2)) -> Optional[AuthUser]:
    if not token:
        return None
    try:
        # Your token validation logic here
        return await get_auth_user(token)
    except Exception:
        return None  # Don't raise here if optional


def verify_api_key(api_key: str = Header(..., alias="API-KEY")):
    if api_key != config.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")


def verify_db_key(api_key: str = Header(..., alias="DB-KEY")):
    if api_key != config.DATABASE_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
