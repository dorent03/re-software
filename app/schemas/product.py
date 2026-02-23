"""Product request/response schemas."""

from pydantic import BaseModel, Field, validator
from typing import Optional

from app.core.config import settings


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    unit: str = Field(default="Stück", max_length=50)
    unit_price: float = Field(..., gt=0, description="Price per unit in EUR")
    vat_rate: float = Field(default=0.19, description="VAT rate as decimal (0.19, 0.07, or 0.0)")

    @validator("vat_rate")
    def validate_vat_rate(cls, value: float) -> float:
        if value not in settings.ALLOWED_VAT_RATES:
            raise ValueError(f"VAT rate must be one of {settings.ALLOWED_VAT_RATES}")
        return value


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    unit: Optional[str] = Field(None, max_length=50)
    unit_price: Optional[float] = Field(None, gt=0)
    vat_rate: Optional[float] = None
    is_active: Optional[bool] = None

    @validator("vat_rate")
    def validate_vat_rate(cls, value: Optional[float]) -> Optional[float]:
        if value is not None and value not in settings.ALLOWED_VAT_RATES:
            raise ValueError(f"VAT rate must be one of {settings.ALLOWED_VAT_RATES}")
        return value


class ProductResponse(BaseModel):
    id: str
    company_id: str
    name: str = ""
    description: str = ""
    unit: str = "Stück"
    unit_price: float = 0.0
    vat_rate: float = 0.19
    is_active: bool = True

    class Config:
        orm_mode = True

    def __init__(self, **data):
        for field in ("name", "description", "unit"):
            if data.get(field) is None:
                data[field] = ""
        super().__init__(**data)
