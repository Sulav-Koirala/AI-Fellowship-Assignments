from pydantic import BaseModel
from typing import Optional

class OfficeBase(BaseModel):
    city : str
    phone : str
    address_line1 : str
    address_line2 : Optional[str]
    state : Optional[str]
    country : str
    postal_code : str
    territory : str

    class Config:
        from_attributes = True

class OfficeCreate(OfficeBase):
    office_code: str

class OfficeUpdate(OfficeBase):
    city : Optional[str] = None
    phone : Optional[str] = None
    address_line1 : Optional[str] = None
    address_line2 : Optional[str] = None
    state : Optional[str] = None
    country : Optional[str] = None
    postal_code : Optional[str] = None
    territory : Optional[str] = None

    class Config:
        from_attributes = True

class OfficeOut(OfficeCreate):
    pass