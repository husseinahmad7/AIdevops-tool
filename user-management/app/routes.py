from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import uuid
from datetime import datetime, timedelta
from typing import List

from . import models, schemas, crud, auth
from .database import get_db

router = APIRouter()


# Authentication routes
@router.post("/auth/login", response_model=schemas.Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last login time
    crud.update_last_login(db, user.id)

    # Create access token
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username, "user_id": str(user.id), "role": user.role},
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/auth/register", response_model=schemas.User)
async def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    return crud.create_user(db, user)


# User routes
@router.get("/users/me", response_model=schemas.User)
async def read_users_me(
    current_user: models.User = Depends(auth.get_current_active_user),
):
    return current_user


@router.put("/users/me", response_model=schemas.User)
async def update_user_me(
    user: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    return crud.update_user(db, current_user.id, user)


# Aliases to align with spec sample endpoints
@router.get("/users/profile", response_model=schemas.User)
async def read_users_profile(
    current_user: models.User = Depends(auth.get_current_active_user),
):
    return current_user


@router.put("/users/profile", response_model=schemas.User)
async def update_users_profile(
    user: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    return crud.update_user(db, current_user.id, user)


@router.get("/users/validate")
async def validate_user(
    current_user: models.User = Depends(auth.get_current_active_user),
):
    return {
        "id": str(current_user.id),
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
        "is_active": current_user.is_active,
    }


# Admin user routes
@router.get("/users", response_model=List[schemas.User])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_admin_user),
):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@router.get("/users/{user_id}", response_model=schemas.User)
async def read_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_admin_user),
):
    db_user = crud.get_user(db, uuid.UUID(user_id))
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.put("/users/{user_id}", response_model=schemas.User)
async def update_user(
    user_id: str,
    user: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_admin_user),
):
    return crud.update_user(db, uuid.UUID(user_id), user)


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_admin_user),
):
    return crud.delete_user(db, uuid.UUID(user_id))


# API Key routes
@router.post("/users/me/api-keys", response_model=schemas.APIKey)
async def create_api_key_for_me(
    api_key: schemas.APIKeyCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    return crud.create_api_key(db, api_key, current_user.id)


@router.get("/users/me/api-keys", response_model=List[schemas.APIKeyInDB])
async def read_api_keys_for_me(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    api_keys = crud.get_api_keys_by_user(db, current_user.id, skip=skip, limit=limit)
    return api_keys


@router.delete("/users/me/api-keys/{api_key_id}")
async def delete_api_key_for_me(
    api_key_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    return crud.delete_api_key(db, uuid.UUID(api_key_id), current_user.id)


# Admin API Key routes
@router.get("/users/{user_id}/api-keys", response_model=List[schemas.APIKeyInDB])
async def read_api_keys(
    user_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_admin_user),
):
    api_keys = crud.get_api_keys_by_user(db, uuid.UUID(user_id), skip=skip, limit=limit)
    return api_keys
