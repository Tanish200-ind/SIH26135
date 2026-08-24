"""Security helpers: password hashing, JWT creation/validation, RBAC guards.

This is the single source of truth for how demo passwords are hashed and how
JWTs are signed/verified. ``scripts/seed_demo_data.py`` reuses ``hash_password``
here so stored hashes verify against the login endpoint.
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.app.config import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY
from backend.app.database.models import User
from backend.app.database.session import get_db

# ---------------------------------------------------------------------------
# Password hashing (must match what the seed script stored)
# ---------------------------------------------------------------------------
_PBKDF2_SALT = b"sih26135-demo-salt"
_PBKDF2_ITERATIONS = 100_000


def hash_password(password: str) -> str:
    """PBKDF2-SHA256 hex digest (Python stdlib only)."""
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), _PBKDF2_SALT, _PBKDF2_ITERATIONS
    ).hex()


def verify_password(plain: str, password_hash: str) -> bool:
    """Constant-time comparison of a candidate password against a stored hash."""
    return secrets.compare_digest(hash_password(plain), password_hash)


# ---------------------------------------------------------------------------
# JWT creation / validation
# ---------------------------------------------------------------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def create_access_token(
    subject: Union[int, str],
    role: str,
    email: str,
    expires_minutes: Optional[int] = None,
) -> str:
    """Create a signed JWT with ``sub`` (user id), ``role`` and ``email`` claims."""
    lifetime = expires_minutes or ACCESS_TOKEN_EXPIRE_MINUTES
    expire = datetime.now(timezone.utc) + timedelta(minutes=lifetime)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "role": role,
        "email": email,
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """Decode a JWT. Raises 401 if missing/expired/signed wrongly."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the authenticated ``User`` from the Bearer token."""
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token)
    subject = payload.get("sub")
    if subject is None:
        raise credentials_exc
    try:
        user_id = int(subject)
    except (TypeError, ValueError):
        raise credentials_exc
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exc
    return user


# ---------------------------------------------------------------------------
# Role-based access control
# ---------------------------------------------------------------------------
def require_roles(*roles: str):
    """Return a FastAPI dependency that allows only the given roles."""

    def _guard(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions for your role",
            )
        return current_user

    return _guard