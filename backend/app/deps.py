"""
deps.py
-------
FastAPI dependency providers.

Changes from original:
- Added explicit return type annotation.
- Improved error message clarity.
- get_current_user now logs failed auth attempts for audit trail.
"""

import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .auth import decode_access_token
from .database import get_db
from .models import User

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Decode the Bearer JWT and return the corresponding User row.
    Raises HTTP 401 if the token is missing, invalid, expired, or the user
    no longer exists in the database.
    """
    user_id = decode_access_token(token)
    if not user_id:
        logger.warning("JWT decode failed — invalid or expired token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.get(User, user_id)
    if not user:
        logger.warning("JWT valid but user not found: %s", user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
