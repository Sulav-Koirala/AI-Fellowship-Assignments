from sqlalchemy.orm import Session
from app.models import Product
from app.schemas.product_schemas import ProductCreate, ProductUpdate
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from app.logger import logger

def get_products(db: Session, skip: int = 0, limit: int = 10):
    logger.info(f"Fetching products with offset {skip} and limit {limit}")
    return db.query(Product).offset(skip).limit(limit).all()

def get_product(db: Session, product_code: str):
    logger.info(f"Searching for product with product code {product_code}")
    product = db.query(Product).filter(Product.product_code == product_code).first()
    if not product:
        logger.warning(f"Product {product_code} not found")
        raise HTTPException(status_code=404, detail="Product not found")
    return product

def create_product(db: Session, data: ProductCreate):
    try:
        db_product = Product(**data.model_dump()) 
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        logger.info(f"Created new product with code: {db_product.product_code}")
        return db_product
    except IntegrityError:
        db.rollback()
        logger.error("Foreign Key error occurred")
        raise HTTPException(
            status_code=400, 
            detail="ForeignKey Error"
        )

def update_product(db: Session, product_code: str, data: ProductUpdate):
    try:
        db_product = get_product(db, product_code)
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_product, key, value)
        db.commit()
        db.refresh(db_product)
        logger.info(f"Updated product with code: {db_product.product_code}")
        return db_product
    except IntegrityError:
        db.rollback()
        logger.error("Foreign Key error occurred")
        raise HTTPException(
            status_code=400, 
            detail="ForeignKey Error"
        )

def delete_product(db: Session, product_code: str):
    db_product = get_product(db, product_code)
    db.delete(db_product)
    db.commit()
    logger.info(f"Deleted product with code: {db_product.product_code}")
    return {"message": "Product deleted"}