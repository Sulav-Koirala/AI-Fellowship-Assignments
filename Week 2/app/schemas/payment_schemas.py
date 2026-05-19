from pydantic import BaseModel
from typing import Optional
from datetime import date
from decimal import Decimal

class PaymentSchema(BaseModel):
    check_number: str
    amount: float
    class Config:
        from_attributes = True

class PaymentBase(BaseModel):
    payment_date: date
    amount: Decimal

    class Config:
        from_attributes = True

class PaymentCreate(PaymentBase):
    customer_number: int
    check_number: str

class PaymentUpdate(BaseModel):
    payment_date: Optional[date] = None
    amount: Optional[Decimal] = None

    class Config:
        from_attributes = True

class PaymentOut(PaymentCreate):
    pass