from pydantic import BaseModel
from typing import Optional

class ProductlineBase(BaseModel):
    product_line: str
    text_description: Optional[str] = None
    html_description: Optional[str] = None
    image: Optional[bytes] = None

    class Config:
        from_attributes = True

class ProductlineCreate(ProductlineBase):
    pass

class ProductlineUpdate(BaseModel):
    product_line: Optional[str] = None
    text_description: Optional[str] = None
    html_description: Optional[str] = None
    image: Optional[bytes] = None

    class Config:
        from_attributes = True

class ProductlineOut(ProductlineBase):
    pass
    