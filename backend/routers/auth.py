from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas
from core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,
    get_current_user,
)
from config import settings

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/register", response_model=schemas.UserResponse, status_code=201)
def register(data: schemas.UserRegisterRequest, db: Session = Depends(get_db)):
    """Register a new user. Spec: USR-01."""
    existing = db.query(models.User).filter(models.User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="El correo ya está registrado")

    user = models.User(
        full_name=data.full_name,
        email=data.email,
        hashed_password=hash_password(data.password),
        role=models.UserRole.STUDENT,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=schemas.TokenResponse)
def login(data: schemas.UserLoginRequest, db: Session = Depends(get_db)):
    """Authenticate and issue JWT tokens. Spec: USR-02."""
    user = db.query(models.User).filter(models.User.email == data.email).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    if not user.is_active:
        raise HTTPException(status_code=401, detail="Cuenta inactiva")

    token_data = {"sub": str(user.id), "role": user.role.value}
    return schemas.TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


@router.post("/refresh", response_model=schemas.AccessTokenResponse)
def refresh_token(data: schemas.RefreshTokenRequest, db: Session = Depends(get_db)):
    """Issue new access token from refresh token. Spec: USR-02-C."""
    payload = decode_token(data.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Token de refresco inválido o expirado")

    user_id = payload.get("sub")
    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Token de refresco inválido o expirado")

    token_data = {"sub": str(user.id), "role": user.role.value}
    return schemas.AccessTokenResponse(access_token=create_access_token(token_data))
