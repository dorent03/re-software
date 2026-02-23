"""Statistics response schemas."""

from pydantic import BaseModel
from typing import List


class MonthlyRevenue(BaseModel):
    year: int
    month: int
    total_gross: float
    total_net: float
    total_vat: float
    invoice_count: int


class CustomerRevenue(BaseModel):
    customer_id: str
    customer_name: str = ""
    total_gross: float
    total_net: float
    invoice_count: int


class MonthlyRevenueResponse(BaseModel):
    data: List[MonthlyRevenue]


class CustomerRevenueResponse(BaseModel):
    data: List[CustomerRevenue]
