from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.office_schemas import OfficeCreate, OfficeOut, OfficeUpdate
from app.crud import office_crud
from typing import List
from app.logger import logger

router = APIRouter(prefix="/offices", tags=["Offices"])

@router.get("/", response_model=List[OfficeOut])
def read_offices(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    logger.info("Request received: GET /offices")
    return office_crud.get_offices(db, skip, limit)

@router.get("/{office_code}", response_model=OfficeOut)
def read_office(office_code: str, db: Session = Depends(get_db)):
    logger.info(f"Request received: GET /offices/{office_code}")
    return office_crud.get_office(db, office_code)

@router.post("/create", response_model=OfficeOut)
def create_office(office: OfficeCreate, db: Session = Depends(get_db)):
    logger.info("Request received: POST /offices/create")
    return office_crud.create_office(db, office)

@router.put("/update/{office_code}", response_model=OfficeOut)
def update_office(office_code: str, office: OfficeUpdate, db: Session = Depends(get_db)):
    logger.info(f"Request received: PUT /offices/update/{office_code}")
    return office_crud.update_office(db, office_code, office)

@router.delete("/delete/{office_code}")
def delete_office(office_code: str, db: Session = Depends(get_db)):
    logger.info(f"Request received: DELETE /offices/delete/{office_code}")
    return office_crud.delete_office(db, office_code)