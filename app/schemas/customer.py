"""Customer request/response schemas."""

from pydantic import BaseModel, Field
from typing import Optional


class CustomerCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    street: str = Field(..., min_length=1, max_length=200)
    zip_code: str = Field(..., min_length=1, max_length=20)
    city: str = Field(..., min_length=1, max_length=100)
    country: str = Field(default="DE", max_length=5)
    email: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=30)
    tax_id: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = Field(None, max_length=1000)


class CustomerUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    street: Optional[str] = Field(None, max_length=200)
    zip_code: Optional[str] = Field(None, max_length=20)
    city: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=5)
    email: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=30)
    tax_id: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = Field(None, max_length=1000)
    is_active: Optional[bool] = None


class CustomerResponse(BaseModel):
    id: str
    company_id: str
    name: str
    street: str = ""
    zip_code: str = ""
    city: str = ""
    country: str = "DE"
    email: str = ""
    phone: str = ""
    tax_id: str = ""
    notes: str = ""
    is_active: bool = True

    class Config:
        orm_mode = True

    def __init__(self, **data):
        for field in ("email", "phone", "tax_id", "notes", "street", "zip_code", "city", "country"):
            if data.get(field) is None:
                data[field] = ""
        super().__init__(**data)
