from sqlalchemy.orm import Session
from app.models import Order
from app.schemas.order_schemas import OrderCreate, OrderUpdate
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from app.logger import logger

def get_orders(db: Session, skip: int = 0, limit: int = 10):
    logger.info(f"Fetching orders with offset {skip} and limit {limit}")
    return db.query(Order).offset(skip).limit(limit).all()

def get_order(db: Session, order_number: int):
    logger.info(f"Searching for order with order number {order_number}")
    order = db.query(Order).filter(Order.order_number == order_number).first()
    if not order:
        logger.warning(f"Order {order_number} not found")
        raise HTTPException(status_code=404, detail="Order not found")
    return order

def create_order(db: Session, data: OrderCreate):
    try: 
        db_order = Order(**data.model_dump())
        db.add(db_order)
        db.commit()
        db.refresh(db_order)
        logger.info(f"Created new order with number: {db_order.order_number}")
        return db_order
    except IntegrityError:
        db.rollback()
        logger.error("Foreign Key error occurred")
        raise HTTPException(
            status_code=400, 
            detail="ForeignKey Error"
        )

def update_order(db: Session, order_number: int, data: OrderUpdate):
    try:
        db_order = get_order(db, order_number)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(db_order, key, value)
        db.commit()
        db.refresh(db_order)
        logger.info(f"Updated order with number: {db_order.order_number}")
        return db_order
    except IntegrityError:
        db.rollback()
        logger.error("Foreign Key error occurred")
        raise HTTPException(
            status_code=400, 
            detail="ForeignKey Error"
        )

def delete_order(db: Session, order_number: int):
    db_order = get_order(db, order_number)
    db.delete(db_order)
    db.commit()
    logger.info(f"Deleted order with number: {db_order.order_number}")
    return {"message": "Order deleted"}