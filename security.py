import secrets
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import Depends, Header, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

import crud
from config import API_KEY, JWT_SECRET
from database import get_conn

ALGORITHM = "HS256"
TOKEN_MINUTES = 60

_hasher = PasswordHasher()
# Used when a username does not exist, so login takes the same time either way
_DUMMY_HASH = _hasher.hash("timing-equalizer-password")
_bearer = HTTPBearer(auto_error=False)


# API key: protects the character endpoints
def verify_api_key(x_api_key: str | None = Header(default=None)):
    if x_api_key is None or not secrets.compare_digest(
        x_api_key.encode(), API_KEY.encode()
    ):
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")


# Passwords: only the argon2 hash is ever stored
def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str | None, password: str) -> bool:
    try:
        ok = _hasher.verify(password_hash or _DUMMY_HASH, password)
    except (VerificationError, InvalidHashError):
        ok = False
    return ok and password_hash is not None


# Tokens: signed with JWT_SECRET, expire after TOKEN_MINUTES
def create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=TOKEN_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    conn=Depends(get_conn),
):
    unauthorized = HTTPException(
        status_code=401,
        detail="Invalid or expired token.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[ALGORITHM])
        user_id = int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise unauthorized
    user = crud.get_user_by_id(conn, user_id)
    if user is None or not user["is_active"]:
        raise unauthorized
    return user


def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    conn=Depends(get_conn),
):
    # For public endpoints that add extra detail when a valid token is sent.
    # A missing or bad token just means "not logged in", never an error.
    if credentials is None:
        return None
    try:
        return get_current_user(credentials, conn)
    except HTTPException:
        return None
