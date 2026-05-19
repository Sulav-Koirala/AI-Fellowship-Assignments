from sqlalchemy import Column, Integer, String, ForeignKey, Date, Text, Numeric, SmallInteger
from sqlalchemy.orm import relationship
from app.database import Base

class Order(Base):
    __tablename__ = "orders"

    order_number = Column("orderNumber", Integer, primary_key=True)
    order_date = Column("orderDate", Date, nullable=False)
    required_date = Column("requiredDate", Date, nullable=False)
    shipped_date = Column("shippedDate", Date)
    status = Column(String(15), nullable=False)
    comments = Column(Text)
    customer_number = Column("customerNumber", Integer, ForeignKey("customers.customerNumber"), nullable=False)

    customer = relationship("Customer", back_populates="orders")
    order_details = relationship("OrderDetail", back_populates="order", cascade="all, delete-orphan")

class OrderDetail(Base):
    __tablename__ = "orderdetails"

    order_number = Column("orderNumber", Integer, ForeignKey("orders.orderNumber"), primary_key=True)
    product_code = Column("productCode", String(15), ForeignKey("products.productCode"), primary_key=True)
    quantity_ordered = Column("quantityOrdered", Integer, nullable=False)
    price_each = Column("priceEach", Numeric(10, 2), nullable=False)
    order_line_number = Column("orderLineNumber", SmallInteger, nullable=False)

    order = relationship("Order", back_populates="order_details")
    product = relationship("Product", back_populates="order_details")