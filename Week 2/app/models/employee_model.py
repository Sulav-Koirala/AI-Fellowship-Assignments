from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Employee(Base):
    __tablename__ = "employees"

    employee_number = Column("employeeNumber", Integer, primary_key=True)
    last_name = Column("lastName", String(50), nullable=False)
    first_name = Column("firstName", String(50), nullable=False)
    extension = Column(String(10), nullable=False)
    email = Column(String(100), nullable=False)
    office_code = Column("officeCode", String(10), ForeignKey("offices.officeCode"), nullable=False)
    reports_to = Column("reportsTo", Integer, ForeignKey("employees.employeeNumber", ondelete="SET NULL"))
    job_title = Column("jobTitle", String(50), nullable=False)

    office = relationship("Office", back_populates="employees")
    customers = relationship("Customer", back_populates="employee")
    manager = relationship("Employee", remote_side=[employee_number], back_populates="subordinates")
    subordinates = relationship("Employee", back_populates="manager")