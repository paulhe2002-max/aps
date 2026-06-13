from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ProductCreate(BaseModel):
    code: str
    name: str
    product_type: str = "FG"
    unit: str = "PCS"
    lead_time_days: float = 1.0
    safety_stock: float = 0.0
    description: Optional[str] = None


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    product_type: Optional[str] = None
    unit: Optional[str] = None
    lead_time_days: Optional[float] = None
    safety_stock: Optional[float] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ProductOut(BaseModel):
    id: int
    code: str
    name: str
    product_type: str
    unit: str
    lead_time_days: float
    safety_stock: float
    description: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class BomItemCreate(BaseModel):
    parent_product_id: int
    child_product_id: int
    quantity: float
    unit: str = "PCS"
    scrap_rate: float = 0.0


class BomItemOut(BaseModel):
    id: int
    parent_product_id: int
    child_product_id: int
    quantity: float
    unit: str
    scrap_rate: float
    is_active: bool
    child_product: Optional[ProductOut] = None

    class Config:
        from_attributes = True


class BomTreeNode(BaseModel):
    product: ProductOut
    quantity: float
    scrap_rate: float
    children: List["BomTreeNode"] = []
