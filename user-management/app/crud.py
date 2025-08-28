from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import uuid
from datetime import datetime
import secrets
import string

from . import models, schemas, auth


# User CRUD operations
def get_user(db: Session, user_id: uuid.UUID):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate):
    # Check if username or email already exists
    if get_user_by_username(db, user.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    if get_user_by_email(db, user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Create new user
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password,
        role=user.role,
        created_at=datetime.utcnow(),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, user_id: uuid.UUID, user: schemas.UserUpdate):
    db_user = get_user(db, user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Update user fields if provided
    update_data = user.dict(exclude_unset=True)
    if "password" in update_data:
        update_data["password_hash"] = auth.get_password_hash(
            update_data.pop("password")
        )

    for key, value in update_data.items():
        setattr(db_user, key, value)

    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: uuid.UUID):
    db_user = get_user(db, user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    db.delete(db_user)
    db.commit()
    return {"message": "User deleted successfully"}


# API Key CRUD operations
def generate_api_key():
    # Generate a secure random API key
    alphabet = string.ascii_letters + string.digits
    api_key = "".join(secrets.choice(alphabet) for _ in range(32))
    return api_key


def get_api_key(db: Session, api_key_id: uuid.UUID):
    return db.query(models.APIKey).filter(models.APIKey.id == api_key_id).first()


def get_api_keys_by_user(
    db: Session, user_id: uuid.UUID, skip: int = 0, limit: int = 100
):
    return (
        db.query(models.APIKey)
        .filter(models.APIKey.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_api_key(db: Session, api_key: schemas.APIKeyCreate, user_id: uuid.UUID):
    # Generate API key
    key = generate_api_key()
    key_hash = auth.get_password_hash(key)

    # Create API key in database
    db_api_key = models.APIKey(
        user_id=user_id,
        key_name=api_key.key_name,
        key_hash=key_hash,
        permissions=api_key.permissions,
        expires_at=api_key.expires_at,
        created_at=datetime.utcnow(),
    )
    db.add(db_api_key)
    db.commit()
    db.refresh(db_api_key)

    # Return API key with the actual key (only shown once)
    return schemas.APIKey(
        id=db_api_key.id,
        user_id=db_api_key.user_id,
        key_name=db_api_key.key_name,
        permissions=db_api_key.permissions,
        expires_at=db_api_key.expires_at,
        created_at=db_api_key.created_at,
        key=key,
    )


def delete_api_key(db: Session, api_key_id: uuid.UUID, user_id: uuid.UUID):
    db_api_key = get_api_key(db, api_key_id)
    if not db_api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="API key not found"
        )

    # Check if API key belongs to user
    if db_api_key.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this API key",
        )

    db.delete(db_api_key)
    db.commit()
    return {"message": "API key deleted successfully"}


# Authentication operations
def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user:
        return False
    if not auth.verify_password(password, user.password_hash):
        return False
    return user


def update_last_login(db: Session, user_id: uuid.UUID):
    db_user = get_user(db, user_id)
    if db_user:
        db_user.last_login = datetime.utcnow()
        db.commit()
        db.refresh(db_user)
    return db_user
