from sqlalchemy import Column, Integer, String, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Customer(Base):
    __tablename__ = "customers"
    
    customer_number = Column("customerNumber", Integer, primary_key=True, nullable=False)
    customer_name = Column("customerName", String(50), nullable=False)
    contact_last_name = Column("contactLastName", String(50), nullable=False)
    contact_first_name = Column("contactFirstName", String(50), nullable=False)
    phone = Column(String(50), nullable=False)
    address_line1 = Column("addressLine1", String(50), nullable=False)
    address_line2 = Column("addressLine2", String(50), nullable=True)
    city = Column(String(50), nullable=False)
    state = Column(String(50), nullable=True)
    postal_code = Column("postalCode", String(15), nullable=True)
    country = Column(String(50), nullable=False)
    sales_rep_employee_number = Column("salesRepEmployeeNumber", Integer, ForeignKey("employees.employeeNumber"), nullable=True) 
    credit_limit = Column("creditLimit", Numeric(10, 2), nullable=True)

    orders = relationship("Order", back_populates="customer")
    payments = relationship("Payment", back_populates="customer")
    employee = relationship("Employee", back_populates="customers")