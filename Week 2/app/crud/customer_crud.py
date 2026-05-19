from sqlalchemy.orm import Session,joinedload
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from app.models import Customer
from app.schemas import customer_schemas
from app.logger import logger

def get_customer(db: Session, customer_id: int):
    logger.info(f"Searching for customer ID: {customer_id}")
    return db.query(Customer).options(joinedload(Customer.orders), joinedload(Customer.payments))\
            .filter(Customer.customer_number == customer_id).first()

def get_customers(db: Session, skip: int = 0, limit: int = 10):
    logger.info(f"Fetching customers with offset {skip} and limit {limit}")
    return db.query(Customer).options(joinedload(Customer.orders), joinedload(Customer.payments)).offset(skip).limit(limit).all()

def create_customer(db: Session, customer: customer_schemas.CustomerCreate):
    try:
        db_customer = Customer(**customer.model_dump())
        db.add(db_customer)
        db.commit()
        db.refresh(db_customer)
        logger.info(f"Created new customer with ID: {db_customer.customer_number}")
        return db_customer
    except IntegrityError:
        db.rollback()
        logger.error("Foreign Key error occurred")
        raise HTTPException(
            status_code=400, 
            detail="ForeignKey Error"
        )