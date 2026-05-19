from sqlalchemy.orm import Session
from app.models import Office,Employee
from app.schemas.office_schemas import OfficeCreate, OfficeUpdate
from fastapi import HTTPException
from app.logger import logger

def get_offices(db: Session, skip: int = 0, limit: int = 10):
    logger.info(f"Fetching offices with offset {skip} and limit {limit}")
    return db.query(Office).offset(skip).limit(limit).all()

def get_office(db: Session, office_code: str):
    logger.info(f"Searching for office with office code {office_code}")
    office = db.query(Office).filter(Office.office_code == office_code).first()
    if not office:
        logger.warning(f"Office {office_code} not found")
        raise HTTPException(status_code=404, detail="Office not found")
    return office

def create_office(db: Session, data: OfficeCreate):
    db_office = Office(**data.model_dump())
    db.add(db_office)
    db.commit()
    db.refresh(db_office)
    logger.info(f"Created new office with code: {db_office.office_code}")
    return db_office

def update_office(db: Session, office_code: str, data: OfficeUpdate):
    db_office = get_office(db, office_code)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(db_office, key, value)
    db.commit()
    db.refresh(db_office)
    logger.info(f"Updated office with code: {db_office.office_code}")
    return db_office

def delete_office(db: Session, office_code: str):
    employee_count = db.query(Employee).filter(Employee.office_code == office_code).count()
    if employee_count > 0:
        logger.warning("Can't delete an office to which employees are assigned")
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot delete office. {employee_count} employees are still assigned to it."
        )
    db_office = db.query(Office).filter(Office.office_code == office_code).first()
    db.delete(db_office)
    db.commit()
    logger.info(f"Deleted office with number: {db_office.office_code}")
    return {"message": "Office deleted successfully"}