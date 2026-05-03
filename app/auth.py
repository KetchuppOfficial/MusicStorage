"""Authentication"""

from datetime import datetime, timedelta, timezone
from jose import jwt
from passlib.context import CryptContext

SECRET_KEY = "secret"
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"])


def hash_password(password: str):
    """Hash password"""
    return pwd_context.hash(password)


def verify_password(plain, hashed):
    """Verify password"""
    return pwd_context.verify(plain, hashed)


def create_token(data: dict):
    """Create token"""
    to_encode = data.copy()
    to_encode.update({"exp": datetime.now(timezone.utc) + timedelta(hours=2)})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
