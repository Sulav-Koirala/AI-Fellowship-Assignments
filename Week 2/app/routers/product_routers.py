from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.product_schemas import ProductCreate, ProductOut, ProductUpdate
from app.crud import product_crud
from typing import List
from app.logger import logger

router = APIRouter(prefix="/products", tags=["Products"])

@router.get("/", response_model=List[ProductOut])
def read_products(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    logger.info("Request received: GET /products")
    return product_crud.get_products(db, skip, limit)

@router.get("/{product_code}", response_model=ProductOut)
def read_product(product_code: str, db: Session = Depends(get_db)):
    logger.info(f"Request received: GET /products/{product_code}")
    return product_crud.get_product(db, product_code)

@router.post("/create", response_model=ProductOut)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    logger.info("Request received: POST /products/create")
    return product_crud.create_product(db, product)

@router.put("/update/{product_code}", response_model=ProductOut)
def update_product(product_code: str, product: ProductUpdate, db: Session = Depends(get_db)):
    logger.info(f"Request received: PUT /products/update/{product_code}")
    return product_crud.update_product(db, product_code, product)

@router.delete("/delete/{product_code}")
def delete_product(product_code: str, db: Session = Depends(get_db)):
    logger.info(f"Request received: DELETE /products/delete/{product_code}")
    return product_crud.delete_product(db, product_code)