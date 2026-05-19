from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.payment_schemas import PaymentCreate, PaymentOut, PaymentUpdate
from app.crud import payment_crud
from typing import List
from app.logger import logger

router = APIRouter(prefix="/payments", tags=["Payments"])

@router.get("/", response_model=List[PaymentOut])
def read_payments(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    logger.info("Request received: GET /payments")
    return payment_crud.get_payments(db, skip, limit)

@router.get("/{customer_number}/{check_number}", response_model=PaymentOut)
def read_payment(customer_number: int, check_number: str, db: Session = Depends(get_db)):
    logger.info(f"Request received: GET /payments/{customer_number}/{check_number}")
    return payment_crud.get_payment(db, customer_number, check_number)

@router.post("/create", response_model=PaymentOut)
def create_payment(payment: PaymentCreate, db: Session = Depends(get_db)):
    logger.info("Request received: POST /payments/create")
    return payment_crud.create_payment(db, payment)

@router.put("/update/{customer_number}/{check_number}", response_model=PaymentOut)
def update_payment(customer_number: int, check_number: str, payment: PaymentUpdate, db: Session = Depends(get_db)):
    logger.info(f"Request received: PUT /payments/update/{customer_number}/{check_number}")
    return payment_crud.update_payment(db, customer_number, check_number, payment)

@router.delete("/delete/{customer_number}/{check_number}")
def delete_payment(customer_number: int, check_number: str, db: Session = Depends(get_db)):
    logger.info(f"Request received: DELETE /payments/delete/{customer_number}/{check_number}")
    return payment_crud.delete_payment(db, customer_number, check_number)