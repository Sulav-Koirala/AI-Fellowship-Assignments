from pydantic import BaseModel
from typing import Optional
from decimal import Decimal

class OrderDetailBase(BaseModel):
    quantity_ordered: int
    price_each: Decimal
    order_line_number: int

    class Config:
        from_attributes = True

class OrderDetailCreate(OrderDetailBase):
    order_number: int
    product_code: str

class OrderDetailUpdate(BaseModel):
    quantity_ordered: Optional[int] = None
    price_each: Optional[Decimal] = None
    order_line_number: Optional[int] = None

    class Config:
        from_attributes = True

class OrderDetailOut(OrderDetailCreate):
    pass