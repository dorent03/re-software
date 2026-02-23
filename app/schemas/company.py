"""Company request/response schemas."""

from pydantic import BaseModel, Field
from typing import List, Optional


class CompanyUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    street: Optional[str] = Field(None, max_length=200)
    zip_code: Optional[str] = Field(None, max_length=20)
    city: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=5)
    tax_id: Optional[str] = Field(None, max_length=50)
    phone: Optional[str] = Field(None, max_length=30)
    email: Optional[str] = Field(None, max_length=100)
    website: Optional[str] = Field(None, max_length=200)
    bank_name: Optional[str] = Field(None, max_length=100)
    iban: Optional[str] = Field(None, max_length=34)
    bic: Optional[str] = Field(None, max_length=11)
    is_kleinunternehmer: Optional[bool] = None
    vat_rates: Optional[List[float]] = None
    default_vat_rate: Optional[float] = None


class CompanyResponse(BaseModel):
    id: str
    name: str = ""
    street: str = ""
    zip_code: str = ""
    city: str = ""
    country: str = "DE"
    tax_id: str = ""
    phone: str = ""
    email: str = ""
    website: str = ""
    bank_name: str = ""
    iban: str = ""
    bic: str = ""
    logo_path: str = ""
    is_kleinunternehmer: bool = False
    vat_rates: List[float] = [0.19, 0.07, 0.0]
    default_vat_rate: float = 0.19

    class Config:
        orm_mode = True

    def __init__(self, **data):
        str_fields = (
            "name", "street", "zip_code", "city", "country", "tax_id",
            "phone", "email", "website", "bank_name", "iban", "bic", "logo_path",
        )
        for field in str_fields:
            if data.get(field) is None:
                data[field] = ""
        super().__init__(**data)
