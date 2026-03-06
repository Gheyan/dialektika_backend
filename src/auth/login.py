from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

import os
from dotenv import load_dotenv
from .token import Token, TokenData

from database.models import User
from database.database import AsyncSessionLocal
from .public_user import PublicUser

from sqlalchemy import select


load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 30

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="rest/login")


def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password):
    return password_hash.hash(password)

async def get_real_user(username: str):
    async with AsyncSessionLocal() as db:
        stmt = select(User).where(User.username == username)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

async def get_user(username: str):
    async with AsyncSessionLocal() as db:
        stmt = select(User).where(User.username == username)
        result = await db.execute(stmt)
        user_obj = result.scalar_one_or_none()
        if not user_obj:
            return None
        return PublicUser.model_validate(user_obj)


async def authenticate_user(username: str, password: str):
    user = await get_real_user(username)
    if not user:
        return False
    if not verify_password(password, user.hash):
        return False
    return user


def create_token(data: dict,
                        expires_delta: timedelta | None = None,
                        token_type: str = "access"):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire, "type": token_type})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception

    user = await get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[PublicUser, Depends(get_current_user)],
):
    return current_user


async def verify_refresh_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            return None
        return payload.get("sub")
    except InvalidTokenError:
        return None


async def verify_token_and_get_user(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None or payload.get("type") != "access":
            return None
        user = await get_user(username=username)
        return user

    except (InvalidTokenError, Exception):
        return None