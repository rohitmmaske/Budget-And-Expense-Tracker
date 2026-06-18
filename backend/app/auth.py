"""
auth.py
-------
Password hashing and JWT utilities.

Security notes:
- Passwords are hashed with PBKDF2-HMAC-SHA256 (260 000 iterations) — no external dep.
- JWT tokens are signed with HS256 by default; algorithm is configurable via JWT_ALGORITHM.
- SECRET_KEY must be set in .env for production. A default placeholder is provided for
  local development only and will trigger a startup warning.
- hmac.compare_digest is used for constant-time comparison to prevent timing attacks.
"""

import hashlib
import hmac
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt

logger = logging.getLogger(__name__)

SECRET_KEY: str = os.getenv("SECRET_KEY", "CHANGE_ME_TO_A_LONG_RANDOM_SECRET")
ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
PASSWORD_ITERATIONS: int = 260_000

if SECRET_KEY == "CHANGE_ME_TO_A_LONG_RANDOM_SECRET":
    logger.warning(
        "SECRET_KEY is using the insecure default. "
        "Set SECRET_KEY in backend/.env before deploying to production."
    )


# ---------------------------------------------------------------------------
# Password utilities
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    """Return a PBKDF2-SHA256 hash string in the format:
    ``pbkdf2_sha256$<iterations>$<salt_hex>$<digest_hex>``
    """
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PASSWORD_ITERATIONS,
    )
    return f"pbkdf2_sha256${PASSWORD_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    """Constant-time password verification against a stored hash."""
    try:
        algorithm, iterations_str, salt_hex, stored_digest = password_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        new_digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(iterations_str),
        ).hex()
        return hmac.compare_digest(new_digest, stored_digest)
    except Exception:
        return False


# ---------------------------------------------------------------------------
# JWT utilities
# ---------------------------------------------------------------------------

def create_access_token(subject: str) -> str:
    """Create a signed JWT with ``sub`` set to *subject* (user ID)."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[str]:
    """Decode a JWT and return the ``sub`` claim, or ``None`` on failure."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None
