from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime


class InventoryCreate(BaseModel):
    product_id: int
    actual_stock: float = 0.0
    in_transit: float = 0.0
    wip: float = 0.0
    last_updated: Optional[date] = None
    notes: Optional[str] = None


class InventoryUpdate(BaseModel):
    actual_stock: Optional[float] = None
    in_transit: Optional[float] = None
    wip: Optional[float] = None
    last_updated: Optional[date] = None
    notes: Optional[str] = None


class InventoryOut(BaseModel):
    id: int
    product_id: int
    actual_stock: float
    in_transit: float
    wip: float
    last_updated: Optional[date]
    notes: Optional[str]
    updated_at: datetime
    product_name: Optional[str] = None
    product_code: Optional[str] = None
    safety_stock: Optional[float] = None

    class Config:
        from_attributes = True
