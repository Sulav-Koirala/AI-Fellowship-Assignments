from pydantic import BaseModel
from typing import Optional
from decimal import Decimal

class ProductBase(BaseModel):
    product_name: str
    product_line: str
    product_scale: str
    product_vendor: str
    product_description: str
    quantity_in_stock: int
    buy_price: Decimal
    msrp: Decimal

    class Config:
        from_attributes = True

class ProductCreate(ProductBase):
    product_code: str

class ProductUpdate(BaseModel):
    product_name: Optional[str] = None
    product_line: Optional[str] = None
    product_scale: Optional[str] = None
    product_vendor: Optional[str] = None
    product_description: Optional[str] = None
    quantity_in_stock: Optional[int] = None
    buy_price: Optional[Decimal] = None
    msrp: Optional[Decimal] = None

    class Config:
        from_attributes = True

class ProductOut(ProductCreate):
    pass