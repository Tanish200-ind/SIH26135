"""Authentication routes: seeded login + current-user info (see docs/API.md)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database.models import User
from backend.app.database.session import get_db
from backend.app.schemas.auth import LoginRequest, TokenOut, UserOut
from backend.app.security import (
    create_access_token,
    get_current_user,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenOut)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenOut:
    """Authenticate a seeded demo account and return a JWT.

    There is deliberately no public registration endpoint.
    """
    user = db.query(User).filter(User.email == payload.email).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    token = create_access_token(subject=user.id, role=user.role, email=user.email)
    return TokenOut(access_token=token, role=user.role, email=user.email)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)) -> User:
    """Return the currently authenticated user's identity and role."""
    return current_user