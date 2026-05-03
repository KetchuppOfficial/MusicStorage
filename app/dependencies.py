"""Getters for DB"""

from fastapi import HTTPException
from jose import jwt
from sqlalchemy.orm import Session
from .database import SESSION_LOCAL
from .models import User
from .auth import SECRET_KEY, ALGORITHM


def get_db():
    """Get a DB instance"""
    db = SESSION_LOCAL()
    try:
        yield db
    finally:
        db.close()


def get_current_user(token: str, db: Session):
    """Get current user"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user = db.query(User).filter(User.username == payload["sub"]).first()
        return user
    except Exception as ex:
        raise HTTPException(status_code=401, detail="Invalid token") from ex
