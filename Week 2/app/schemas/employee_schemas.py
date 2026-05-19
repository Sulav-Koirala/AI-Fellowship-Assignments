from pydantic import BaseModel
from typing import Optional

class EmployeeBase(BaseModel):
    last_name: str
    first_name: str
    extension: str
    email: str
    office_code: str
    reports_to: Optional[int] = None
    job_title: str

    class Config:
        from_attributes = True

class EmployeeCreate(EmployeeBase):
    employee_number: int

class EmployeeUpdate(BaseModel):
    last_name: Optional[str] = None
    first_name: Optional[str] = None
    extension: Optional[str] = None
    email: Optional[str] = None
    office_code: Optional[str] = None
    reports_to: Optional[int] = None
    job_title: Optional[str] = None

    class Config:
        from_attributes = True

class EmployeeOut(EmployeeCreate):
    pass