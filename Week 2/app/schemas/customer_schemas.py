from pydantic import BaseModel
from typing import Optional,List
from decimal import Decimal
from app.schemas.order_schemas import OrderSchema
from app.schemas.payment_schemas import PaymentSchema

class CustomerBase(BaseModel):
    customer_name : str
    contact_last_name : str
    contact_first_name : str
    phone : str
    address_line1: str
    address_line2: Optional[str] = None
    city : str
    state: Optional[str] = None
    country : str
    postal_code: Optional[str] = None
    sales_rep_employee_number : Optional[int] = None
    credit_limit : Optional[Decimal] = None
    class Config:
        from_attributes = True

class CustomerCreate(CustomerBase):
    customer_number : int

class CustomerUpdate(BaseModel):
    customer_name : Optional[str] = None
    contact_last_name : Optional[str] = None
    contact_first_name : Optional[str] = None
    phone : Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city : Optional[str] = None
    state: Optional[str] = None
    country : Optional[str] = None
    postal_code: Optional[str] = None
    sales_rep_employee_number : Optional[int] = None
    credit_limit : Optional[Decimal] = None

    class Config:
        from_attributes = True

class CustomerOut(CustomerCreate):
    orders : List[OrderSchema] = []
    payments : List[PaymentSchema] = []