from datetime import timedelta

from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.sql import func
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import status, HTTPException, APIRouter, Depends

from src.database.models import User
from src.auth.schemas import (
    AuthUserListResponseModel,
    AuthChangePasswordModel,
    AuthResetPasswordModel,
    AuthRegisterModel,
    AuthLoginResponse,
    AuthEditUserModel,
    AuthUser,
)
from src.database import get_db
from src.config import config
from src.auth import create_access_token, authenticate_user, verify_password, format_username, get_admin_user, hash_password, get_auth_user

# Router
router = APIRouter()


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    name="Login",
    response_model=AuthLoginResponse,
)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, format_username(form_data.username), form_data.password)
    if not user or not isinstance(user, User):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Update last login time
    user.last_login = func.now()
    # Commit changes
    db.commit()
    # Expires Token
    if "remember_me" in form_data.scopes:
        access_token_expires = timedelta(days=config.JWT_ACCESS_TOKEN_EXPIRE_DAYS)
    else:
        access_token_expires = timedelta(minutes=config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    # Generate Access Token
    access_token = create_access_token(
        data={
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "is_admin": user.is_admin,
        },
        expires_delta=access_token_expires,
    )
    # Return Token
    return {"success": True, "access_token": access_token}


@router.get(
    "/get-user",
    status_code=status.HTTP_200_OK,
    name="Get User",
    dependencies=[Depends(get_auth_user)],
    response_model=AuthUser,
)
async def get_user(user: AuthUser = Depends(get_auth_user)):
    # Return User
    return user


@router.post(
    "/change-password",
    status_code=status.HTTP_200_OK,
    name="Change Password",
    dependencies=[Depends(get_auth_user)],
    response_model=dict[str, bool],
)
async def change_user_password(data: AuthChangePasswordModel, db: Session = Depends(get_db), user: AuthUser = Depends(get_auth_user)):
    # Get User
    db_user = db.execute(select(User).where(User.username == user.username)).scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    # Verify old password
    if not verify_password(data.old_password, db_user.password):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incorrect password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Hash new password
    db_user.password = hash_password(data.confirm_password)
    db_user.updated_at = func.now()

    # Commit changes
    db.commit()

    # Return Success
    return {"success": True}


@router.post(
    "/edit-user",
    status_code=status.HTTP_200_OK,
    name="Edit User",
    dependencies=[Depends(get_auth_user)],
    response_model=dict[str, bool],
)
async def edit_user(data: AuthEditUserModel, db: Session = Depends(get_db), user: AuthUser = Depends(get_auth_user)):
    # Get User
    db_user = db.execute(select(User).where(User.username == user.username)).scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Hash new password
    db_user.email = data.email
    db_user.first_name = data.first_name
    db_user.last_name = data.last_name
    db_user.updated_at = func.now()

    # Commit changes
    db.commit()

    # Return Success
    return {"success": True}


@router.get(
    "/get-all-users",
    status_code=status.HTTP_200_OK,
    name="Change Password",
    dependencies=[Depends(get_admin_user)],
    response_model=list[AuthUserListResponseModel],
)
async def update_user(db: Session = Depends(get_db), user: AuthUser = Depends(get_admin_user)):
    # Get User
    db_users = db.execute(select(User)).scalars().all()
    # Return Success
    return db_users


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    name="Register",
    dependencies=[Depends(get_admin_user)],
    response_model=dict[str, bool],
)
async def add_user(data: AuthRegisterModel, db: Session = Depends(get_db)):
    # Validate if User Exists
    user_exists = db.execute(select(User).where(User.username == format_username(data.username))).scalar_one_or_none()
    if user_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )

    # Create a new User
    user = User(
        username=format_username(data.username),
        password=hash_password(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        email=data.email,
        enabled=True,
    )
    db.add(user)
    db.commit()

    # Return Success
    return {"success": True}


@router.post(
    "/reset-password",
    status_code=status.HTTP_200_OK,
    name="Reset Password",
    dependencies=[Depends(get_admin_user)],
    response_model=dict[str, bool],
)
async def reset_user_password(data: AuthResetPasswordModel, db: Session = Depends(get_db)):
    # Get User
    db_user = db.execute(select(User).where(User.username == data.username)).scalar_one_or_none()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Hash new password
    db_user.password = hash_password(data.confirm_password)
    db_user.updated_at = func.now()

    # Commit changes
    db.commit()

    # Return Success
    return {"success": True}
