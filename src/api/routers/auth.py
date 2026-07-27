import hashlib
import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from src.alerts.email import send_password_reset_email
from src.api.dependencies import create_access_token, get_db, get_current_user
from src.api.rate_limit import limiter
from src.api.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
)
from src.api.schemas.profile import ProfileResponse
from src.config import settings
from src.db.models import User

router = APIRouter(prefix="/auth", tags=["auth"])
_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
RESET_TOKEN_TTL_MINUTES = 60
_GENERIC_FORGOT_MESSAGE = "If an account exists for that email, a password reset link has been sent."


def _hash_token(raw_token: str) -> str:
    # Reset tokens are bearer credentials just like passwords — store only a
    # hash, so a DB leak alone can't be used to redeem an unexpired link.
    return hashlib.sha256(raw_token.encode()).hexdigest()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/hour")
def register(request: Request, body: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(
        email=body.email,
        name=body.name,
        password_hash=_pwd.hash(body.password),
        visa_categories=[],
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenResponse(access_token=create_access_token(user.id))


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(request: Request, body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not user.password_hash or not _pwd.verify(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    return TokenResponse(access_token=create_access_token(user.id))


@router.get("/me", response_model=ProfileResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/forgot-password", response_model=MessageResponse)
@limiter.limit("5/hour")
def forgot_password(request: Request, body: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user:
        # Don't reveal whether this email is registered.
        return MessageResponse(message=_GENERIC_FORGOT_MESSAGE)

    raw_token = secrets.token_urlsafe(32)
    user.reset_token = _hash_token(raw_token)
    user.reset_token_expires = datetime.utcnow() + timedelta(minutes=RESET_TOKEN_TTL_MINUTES)
    db.commit()

    reset_url = f"{settings.frontend_base_url}/reset-password?token={raw_token}"
    send_password_reset_email(user.email, reset_url)
    return MessageResponse(message=_GENERIC_FORGOT_MESSAGE)


@router.post("/reset-password", response_model=MessageResponse)
@limiter.limit("10/minute")
def reset_password(request: Request, body: ResetPasswordRequest, db: Session = Depends(get_db)):
    hashed = _hash_token(body.token)
    user = db.query(User).filter(User.reset_token == hashed).first()
    if not user or not user.reset_token_expires or user.reset_token_expires < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired reset link")

    user.password_hash = _pwd.hash(body.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()
    return MessageResponse(message="Password updated. You can now sign in.")
