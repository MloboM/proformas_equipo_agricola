"""
Esquemas Pydantic para validación de datos
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, validator


class ProductBase(BaseModel):
    brand: str = Field(..., min_length=1, max_length=100)
    model: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="")
    price: float = Field(..., ge=0)
    image_path: Optional[str] = None
    active: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    brand: Optional[str] = Field(None, min_length=1, max_length=100)
    model: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    image_path: Optional[str] = None
    active: Optional[bool] = None


class Product(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ProformaItemBase(BaseModel):
    brand: str
    model: str
    year: Optional[int] = None
    description: str = ""
    qty: int = Field(..., ge=1)
    unit_price: float = Field(..., ge=0)
    currency: str = Field(..., pattern="^(CRC|USD)$")
    image_path: Optional[str] = None
    
    @validator('year')
    def validate_year(cls, v):
        if v is not None and (v < 1900 or v > 2100):
            raise ValueError('El año debe estar entre 1900 y 2100')
        return v


class ProformaItemCreate(ProformaItemBase):
    product_id: Optional[int] = None


class ProformaItem(ProformaItemBase):
    id: int
    line_total: float
    
    class Config:
        from_attributes = True


class ProformaBase(BaseModel):
    number: str = Field(..., min_length=1, max_length=50)
    customer_name: str = Field(..., min_length=1, max_length=200)
    customer_company: Optional[str] = None
    customer_email: Optional[EmailStr] = None
    customer_phone: Optional[str] = None
    customer_address: Optional[str] = None
    customer_attention: Optional[str] = None
    
    advisor_name: Optional[str] = None
    advisor_phone: Optional[str] = None
    advisor_email: Optional[EmailStr] = None
    
    template: str = Field(..., pattern="^(tractor|implement)$")
    validity_days: int = Field(default=15, ge=1, le=365)
    date: datetime = Field(default_factory=datetime.utcnow)
    
    general_terms: Optional[str] = None


class ProformaCreate(ProformaBase):
    items: List[ProformaItemCreate] = Field(..., min_items=1)


class Proforma(ProformaBase):
    id: int
    currency: str
    subtotal: float
    tax: float
    total: float
    created_at: datetime
    pdf_path: Optional[str] = None
    items: List[ProformaItem] = []
    
    class Config:
        from_attributes = True


class TermsBase(BaseModel):
    template: str = Field(..., pattern="^(tractor|implement)$")
    content: str = Field(..., min_length=1)


class TermsCreate(TermsBase):
    pass


class Terms(TermsBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True