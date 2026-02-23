"""Auth-related request/response schemas."""

from pydantic import BaseModel, Field, validator
from typing import Optional


class LoginRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="User password")


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Valid refresh token")


class RegisterRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password (min 8 chars)")
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    company_name: str = Field(..., min_length=1, max_length=200, description="Company name for new tenant")
    company_street: str = Field(..., min_length=1, max_length=200)
    company_zip: str = Field(..., min_length=1, max_length=20)
    company_city: str = Field(..., min_length=1, max_length=100)
    company_country: str = Field(default="DE", max_length=5)

    @validator("email")
    def validate_email(cls, value: str) -> str:
        if "@" not in value or "." not in value.split("@")[-1]:
            raise ValueError("Invalid email format")
        return value.lower().strip()


class UserResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    company_id: str
    role: str
    is_active: bool

    class Config:
        orm_mode = True
