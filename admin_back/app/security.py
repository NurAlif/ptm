from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
from typing import Optional

from . import database, models, schemas
from .config import settings

# This tells FastAPI where the client should go to get the token.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

# --- Password Hashing ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hashed one."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hashes a plain password."""
    return pwd_context.hash(password)


# --- JWT Token Handling ---
def create_access_token(data: dict):
    """
    Creates a JWT access token.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

def verify_access_token(token: str, credentials_exception):
    """
    Verifies a JWT. Decodes it and validates the user ID.
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: Optional[str] = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
        token_data = schemas.TokenData(id=str(user_id))
    except JWTError:
        raise credentials_exception
    return token_data

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    """
    Dependency to get the current user from a token.
    Bypassed: Returns a hardcoded Admin user immediately.
    """
    return models.User(
        id=1,
        username="admin",
        email="admin@example.com",
        realname="Administrator",
        student_id="admin_id",
        group="EG",
        is_admin=True,
        created_at=datetime.utcnow()
    )

def get_current_admin_user(current_user: models.User = Depends(get_current_user)):
    """
    Dependency to ensure the current user is an admin.
    Bypassed: Returns the mocked admin user directly.
    """
    return current_user


# --- REVISED: Dependency for iframe/query parameter authentication ---

def get_current_admin_user_from_query(request: Request, db: Session = Depends(database.get_db)):
    """
    Extracts a token from the URL query parameter.
    Bypassed: Returns a hardcoded Admin user immediately.
    """
    return models.User(
        id=1,
        username="admin",
        email="admin@example.com",
        realname="Administrator",
        student_id="admin_id",
        group="EG",
        is_admin=True,
        created_at=datetime.utcnow()
    )
