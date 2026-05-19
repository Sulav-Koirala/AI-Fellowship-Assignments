from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models import Employee
from app.schemas.employee_schemas import EmployeeCreate, EmployeeUpdate
from fastapi import HTTPException
from app.logger import logger

def get_employees(db: Session, skip: int = 0, limit: int = 10):
    logger.info(f"Fetching employees with offset {skip} and limit {limit}")
    return db.query(Employee).offset(skip).limit(limit).all()

def get_employee(db: Session, employee_number: int):
    logger.info(f"Searching for employee with employee number {employee_number}")
    employee = db.query(Employee).filter(Employee.employee_number == employee_number).first()
    if not employee:
        logger.warning(f"Employee {employee_number} not found")
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee

def create_employee(db: Session, data: EmployeeCreate):
    try:
        db_employee = Employee(**data.model_dump())
        db.add(db_employee)
        db.commit()
        db.refresh(db_employee)
        logger.info(f"Created new employee with number: {db_employee.employee_number}")
        return db_employee
    except IntegrityError:
        db.rollback()
        logger.error("Foreign Key error occurred")
        raise HTTPException(
            status_code=400, 
            detail="ForeignKey Error"
        )

def update_employee(db: Session, employee_number: int, data: EmployeeUpdate):
    try:
        db_employee = get_employee(db, employee_number)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(db_employee, key, value)
        db.commit()
        db.refresh(db_employee)
        logger.info(f"Updated employee with number: {db_employee.employee_number}")
        return db_employee
    except IntegrityError:
        db.rollback()
        logger.error("Foreign Key error occurred")
        raise HTTPException(
            status_code=400, 
            detail="ForeignKey Error"
        )
    
def delete_employee(db: Session, employee_number: int):
    db_employee = get_employee(db, employee_number)
    db.delete(db_employee)
    db.commit()
    logger.info(f"Deleted employee with number: {db_employee.employee_number}")
    return {"message": "Employee deleted"}