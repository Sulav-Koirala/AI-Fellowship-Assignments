from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, Date
from sqlalchemy.orm import relationship
from app.database import Base

class Payment(Base):
    __tablename__ = "payments"

    customer_number = Column("customerNumber", Integer, ForeignKey("customers.customerNumber"), primary_key=True)
    check_number = Column("checkNumber", String(50), primary_key=True)
    payment_date = Column("paymentDate", Date, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)

    customer = relationship("Customer", back_populates="payments")