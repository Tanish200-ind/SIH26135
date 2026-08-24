"""Auth-related request/response schemas (seeded login, JWT)."""

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """JSON body for POST /api/auth/login. Uses the seeded demo accounts."""

    email: EmailStr
    password: str = Field(min_length=1)


class TokenOut(BaseModel):
    """Successful login response: issued JWT + role. Never includes a hash."""

    access_token: str
    token_type: str = "bearer"
    role: str
    email: EmailStr


class UserOut(BaseModel):
    """Public user identity. Deliberately omits password_hash."""

    id: int
    email: EmailStr
    role: str