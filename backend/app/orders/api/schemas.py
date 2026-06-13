from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime


class CustomerOrderCreate(BaseModel):
    order_no: str
    product_id: int
    quantity: float
    due_date: date
    priority: int = 5
    customer_name: Optional[str] = None
    status: str = "open"
    notes: Optional[str] = None


class CustomerOrderUpdate(BaseModel):
    quantity: Optional[float] = None
    due_date: Optional[date] = None
    priority: Optional[int] = None
    customer_name: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class CustomerOrderOut(BaseModel):
    id: int
    order_no: str
    product_id: int
    quantity: float
    due_date: date
    priority: int
    customer_name: Optional[str]
    status: str
    notes: Optional[str]
    created_at: datetime
    product_name: Optional[str] = None
    product_code: Optional[str] = None

    class Config:
        from_attributes = True
