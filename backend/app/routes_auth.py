"""
routes_auth.py
--------------
Authentication endpoints: register, login, and current-user.

Changes from original:
- Added OAuth2 form-data login endpoint (/auth/token) so Swagger UI "Authorize"
  button works correctly (OAuth2PasswordRequestForm sends form data, not JSON).
- Consistent error handling with appropriate HTTP status codes.
- Email is always stored and compared in lowercase.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from .auth import create_access_token, hash_password, verify_password
from .database import get_db
from .deps import get_current_user
from .models import User
from .schemas import TokenOut, UserCreate, UserLogin, UserOut

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Auth"])


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------

@router.post(
    "/register",
    response_model=TokenOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new account",
)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> TokenOut:
    existing = db.scalar(select(User).where(User.email == payload.email.lower()))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    user = User(
        full_name=payload.full_name.strip(),
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("New user registered: %s", user.email)

    token = create_access_token(user.id)
    return TokenOut(access_token=token, user=user)


# ---------------------------------------------------------------------------
# Login — JSON body (used by frontend / Postman)
# ---------------------------------------------------------------------------

@router.post(
    "/login",
    response_model=TokenOut,
    summary="Login with email and password (JSON)",
)
def login(payload: UserLogin, db: Session = Depends(get_db)) -> TokenOut:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(user.id)
    logger.info("User logged in: %s", user.email)
    return TokenOut(access_token=token, user=user)


# ---------------------------------------------------------------------------
# Login — OAuth2 form (used by Swagger UI "Authorize" button)
# ---------------------------------------------------------------------------

@router.post(
    "/token",
    response_model=TokenOut,
    summary="Login via OAuth2 form (Swagger UI)",
    include_in_schema=True,
)
def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenOut:
    """
    Swagger UI sends credentials as form data to the tokenUrl.
    This endpoint accepts that form and returns the same TokenOut shape.
    """
    user = db.scalar(select(User).where(User.email == form_data.username.lower()))
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(user.id)
    return TokenOut(access_token=token, user=user)


# ---------------------------------------------------------------------------
# Current user
# ---------------------------------------------------------------------------

@router.get("/me", response_model=UserOut, summary="Get current user profile")
def me(current_user: User = Depends(get_current_user)) -> UserOut:
    return current_user
