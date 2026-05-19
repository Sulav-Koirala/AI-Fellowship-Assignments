from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.employee_schemas import EmployeeCreate, EmployeeOut, EmployeeUpdate
from app.crud import employee_crud
from typing import List
from app.logger import logger

router = APIRouter(prefix="/employees", tags=["Employees"])

@router.get("/", response_model=List[EmployeeOut])
def read_employees(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    logger.info("Request received: GET /employees")
    return employee_crud.get_employees(db, skip, limit)

@router.get("/{employee_number}", response_model=EmployeeOut)
def read_employee(employee_number: int, db: Session = Depends(get_db)):
    logger.info(f"Request received: GET /employees/{employee_number}")
    return employee_crud.get_employee(db, employee_number)

@router.post("/create", response_model=EmployeeOut)
def create_employee(employee: EmployeeCreate, db: Session = Depends(get_db)):
    logger.info("Request received: POST /employees/create")
    return employee_crud.create_employee(db, employee)

@router.put("/update/{employee_number}", response_model=EmployeeOut)
def update_employee(employee_number: int, employee: EmployeeUpdate, db: Session = Depends(get_db)):
    logger.info(f"Request received: PUT /employees/update/{employee_number}")
    return employee_crud.update_employee(db, employee_number, employee)

@router.delete("/delete/{employee_number}")
def delete_employee(employee_number: int, db: Session = Depends(get_db)):
    logger.info(f"Request received: DELETE /employees/delete/{employee_number}")
    return employee_crud.delete_employee(db, employee_number)