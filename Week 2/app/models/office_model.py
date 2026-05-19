from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from app.database import Base

class Office(Base):
    __tablename__ = "offices"

    office_code = Column("officeCode", String(10), primary_key=True)
    city = Column(String(50), nullable=False)
    phone = Column(String(50), nullable=False)
    address_line1 = Column("addressLine1", String(50), nullable=False)
    address_line2 = Column("addressLine2", String(50))
    state = Column(String(50))
    country = Column(String(50), nullable=False)
    postal_code = Column("postalCode", String(15), nullable=False)
    territory = Column(String(10), nullable=False)

    employees = relationship("Employee", back_populates="office")