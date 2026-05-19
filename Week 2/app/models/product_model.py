from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, Text, LargeBinary
from sqlalchemy.orm import relationship
from app.database import Base

class Product(Base):
    __tablename__ = "products"

    product_code = Column("productCode", String(15), primary_key=True)
    product_name = Column("productName", String(70), nullable=False)
    product_line = Column("productLine", String(50), ForeignKey("productlines.productLine"), nullable=False)
    product_scale = Column("productScale", String(10), nullable=False)
    product_vendor = Column("productVendor", String(50), nullable=False)
    product_description = Column("productDescription", Text, nullable=False)
    quantity_in_stock = Column("quantityInStock", Integer, nullable=False)
    buy_price = Column("buyPrice", Numeric(10, 2), nullable=False)
    msrp = Column("MSRP", Numeric(10, 2), nullable=False)

    product_line_obj = relationship("ProductLine", back_populates="products")
    order_details = relationship("OrderDetail", back_populates="product", cascade="all, delete-orphan")


class ProductLine(Base):
    __tablename__ = "productlines"

    product_line = Column("productLine", String(50), primary_key=True)
    text_description = Column("textDescription", String(4000))
    html_description = Column("htmlDescription", Text)
    image = Column(LargeBinary)

    products = relationship("Product", back_populates="product_line_obj")