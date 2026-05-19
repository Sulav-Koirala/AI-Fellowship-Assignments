from fastapi import FastAPI
from app.routers import count_routers,customer_routers,employee_routers,office_routers,order_routers,\
    payment_routers,product_routers,productline_routers,orderdetail_routers
from app.logger import logger

app = FastAPI()

app.include_router(count_routers.router)

app.include_router(customer_routers.router)
app.include_router(employee_routers.router)
app.include_router(office_routers.router)
app.include_router(order_routers.router)
app.include_router(payment_routers.router)
app.include_router(product_routers.router)
app.include_router(productline_routers.router)
app.include_router(orderdetail_routers.router)

@app.get("/")
def main():
    logger.info("API is fully operating")
    return {"message": "API is fully functional"}