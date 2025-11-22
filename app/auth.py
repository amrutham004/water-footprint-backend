# app/auth.py
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
import os

# secret key (in production, use env var)
SECRET_KEY = os.getenv("JWT_SECRET", "change_this_secret_for_prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hour

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def _truncate_to_72_bytes(password: str) -> (str, bool):
    """
    Truncate input password to at most 72 bytes (bcrypt limit).
    Returns (possibly_truncated_password, truncated_flag).
    We truncate on the UTF-8 bytes and decode ignoring broken byte at the end.
    """
    if password is None:
        return "", False
    if not isinstance(password, str):
        password = str(password)
    b = password.encode("utf-8")
    if len(b) <= 72:
        return password, False
    # truncate bytes safely and decode ignoring errors
    tb = b[:72]
    safe = tb.decode("utf-8", errors="ignore")
    return safe, True

def get_password_hash(password: str) -> str:
    # ensure safe length first
    safe_pwd, _ = _truncate_to_72_bytes(password)
    return pwd_context.hash(safe_pwd)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # When verifying, also truncate the incoming plain password the same way.
    safe_pwd, _ = _truncate_to_72_bytes(plain_password)
    return pwd_context.verify(safe_pwd, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
