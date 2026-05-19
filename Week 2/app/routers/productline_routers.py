from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.productline_schemas import ProductlineCreate, ProductlineOut, ProductlineUpdate
from app.crud import productline_crud
from typing import List
from app.logger import logger

router = APIRouter(prefix="/productlines", tags=["ProductLines"])

@router.get("/", response_model=List[ProductlineOut])
def read_productlines(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    logger.info("Request received: GET /productlines")
    return productline_crud.get_product_lines(db, skip, limit)

@router.get("/{product_line}", response_model=ProductlineOut)
def read_productline(product_line: str, db: Session = Depends(get_db)):
    logger.info(f"Request received: GET /productlines/{product_line}")
    return productline_crud.get_product_line(db, product_line)

@router.post("/create", response_model=ProductlineOut)
def create_productline(product_line: ProductlineCreate, db: Session = Depends(get_db)):
    logger.info("Request received: POST /productlines/create")
    return productline_crud.create_product_line(db, product_line)

@router.put("/update/{product_line}", response_model=ProductlineOut)
def update_productline(product_line: str, data: ProductlineUpdate, db: Session = Depends(get_db)):
    logger.info(f"Request received: PUT /productlines/update/{product_line}")
    return productline_crud.update_product_line(db, product_line, data)

@router.delete("/delete/{product_line}")
def delete_productline(product_line: str, db: Session = Depends(get_db)):
    logger.info(f"Request received: DELETE /productlines/delete/{product_line}")
    return productline_crud.delete_product_line(db, product_line)