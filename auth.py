"""
auth.py — password hashing + JWT helpers for the FastAPI Posts API.

Exposes:
    hash_password(plain)        -> str  (bcrypt hash)
    verify_password(plain, hash) -> bool
    create_token(data)          -> str  (signed JWT, 30-min expiry)
    get_current_user(token)     -> str  (FastAPI dependency; returns the username)

Security note:
    SECRET_KEY is currently a placeholder for local development. In any
    real deployment, load it from an environment variable, e.g.
        import os
        SECRET_KEY = os.environ["JWT_SECRET"]
"""

from datetime import datetime, timedelta
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
SECRET_KEY = "your-secret-key-here"   # TODO: load from env in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# ---------------------------------------------------------------------------
# Password hashing (bcrypt)
# ---------------------------------------------------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Return a bcrypt hash of the given plain-text password."""
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if `plain` matches the bcrypt `hashed` value."""
    return pwd_context.verify(plain, hashed)


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def create_token(data: dict[str, Any]) -> str:
    """
    Encode `data` as a signed JWT with an absolute expiry timestamp.

    Example:
        create_token({"sub": "arshad"})  -> "eyJhbGciOi..."
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """
    FastAPI dependency: decode the bearer token, return the username
    stored in the `sub` claim, or raise 401 on any failure.
    """
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exc
        return username
    except JWTError:
        raise credentials_exc
