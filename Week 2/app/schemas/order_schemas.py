from pydantic import BaseModel
from datetime import date
from typing import Optional,List
from app.schemas.orderdetail_schemas import OrderDetailOut

class OrderSchema(BaseModel):
    order_number: int
    status: str
    class Config:
        from_attributes = True

class OrderBase(BaseModel):
    order_date: date
    required_date: date
    shipped_date: Optional[date] = None
    status: str
    comments: Optional[str] = None
    customer_number: int

    class Config:
        from_attributes = True

class OrderCreate(OrderBase):
    order_number: int

class OrderUpdate(BaseModel):
    order_date: Optional[date] = None
    required_date: Optional[date] = None
    shipped_date: Optional[date] = None
    status: Optional[str] = None
    comments: Optional[str] = None
    customer_number: Optional[int] = None

    class Config:
        from_attributes = True

class OrderOut(OrderCreate):
    order_details: List[OrderDetailOut] = []