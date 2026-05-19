from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
from fastapi import APIRouter,Depends
from app.models import Customer,Order,OrderDetail,Office,Payment,Product,ProductLine,Employee
from app.crud import counts_crud
from app import database
from app.logger import logger

router = APIRouter(prefix="/count", tags=['Counts'])

@router.get("/customers")
async def count_customers(db: AsyncSession = Depends(database.get_async_db)):
    logger.info("Request received: GET /count/customers")
    count =  await counts_crud.get_count(db, Customer)
    return {"customers": count}

@router.get("/orders")
async def count_orders(db: AsyncSession = Depends(database.get_async_db)):
    logger.info("Request received: GET /count/orders")
    count =  await counts_crud.get_count(db, Order)
    return {"orders": count}

@router.get("/payments")
async def count_payments(db: AsyncSession = Depends(database.get_async_db)):
    logger.info("Request received: GET /count/payements")
    count =  await counts_crud.get_count(db, Payment)
    return {"payments": count}

@router.get("/employees")
async def count_employees(db: AsyncSession = Depends(database.get_async_db)):
    logger.info("Request received: GET /count/employees")
    count =  await counts_crud.get_count(db, Employee)
    return {"employees": count}

@router.get("/products")
async def count_products(db: AsyncSession = Depends(database.get_async_db)):
    logger.info("Request received: GET /count/products")
    count =  await counts_crud.get_count(db, Product)
    return {"products": count}

@router.get("/offices")
async def count_offices(db: AsyncSession = Depends(database.get_async_db)):
    logger.info("Request received: GET /count/offices")
    count =  await counts_crud.get_count(db, Office)
    return {"offices": count}

@router.get("/orderdetails")
async def count_orderdetails(db: AsyncSession = Depends(database.get_async_db)):
    logger.info("Request received: GET /count/orderdetails")
    count =  await counts_crud.get_count(db, OrderDetail)
    return {"orderdetails": count}

@router.get("/productlines")
async def count_productlines(db: AsyncSession = Depends(database.get_async_db)):
    logger.info("Request received: GET /count/productlines")
    count =  await counts_crud.get_count(db, ProductLine)
    return {"productlines": count}

@router.get("/overall_counts")
async def get_overall_counts(session_factory=Depends(database.get_async_session_factory)):
    logger.info("Request: Starting concurrent counts")

    async def count(model):
        async with session_factory() as session:
            return await counts_crud.get_count(session, model)

    results = await asyncio.gather(
        count(Customer),
        count(Order),
        count(Product),
        count(Employee),
        count(Office),
        count(Payment),
        count(OrderDetail),
        count(ProductLine),
    )

    return {
        "customers": results[0],
        "orders": results[1],
        "products": results[2],
        "employees": results[3],
        "offices": results[4],
        "payments": results[5],
        "orderdetails": results[6],
        "productlines": results[7],
    }