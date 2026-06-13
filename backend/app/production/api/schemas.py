from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime


class ProductionLineCreate(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    capacity_per_shift: float = 8.0
    shifts_per_day: int = 2
    workers_per_shift: int = 10


class ProductionLineUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    capacity_per_shift: Optional[float] = None
    shifts_per_day: Optional[int] = None
    workers_per_shift: Optional[int] = None
    is_active: Optional[bool] = None


class ProductionLineOut(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str]
    capacity_per_shift: float
    shifts_per_day: int
    workers_per_shift: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class LineProductCreate(BaseModel):
    line_id: int
    product_id: int
    cycle_time_minutes: float
    setup_time_minutes: float = 0.0
    cost_per_unit: float = 0.0


class LineProductOut(BaseModel):
    id: int
    line_id: int
    product_id: int
    cycle_time_minutes: float
    setup_time_minutes: float
    cost_per_unit: float
    is_active: bool
    product_name: Optional[str] = None
    product_code: Optional[str] = None

    class Config:
        from_attributes = True


class WorkingCalendarCreate(BaseModel):
    line_id: int
    work_date: date
    shift_count: int = 2
    available_hours: float = 16.0
    is_holiday: bool = False
    notes: Optional[str] = None


class WorkingCalendarOut(BaseModel):
    id: int
    line_id: int
    work_date: date
    shift_count: int
    available_hours: float
    is_holiday: bool
    notes: Optional[str]

    class Config:
        from_attributes = True


class ChangeoverTimeCreate(BaseModel):
    line_id: int
    from_product_id: int
    to_product_id: int
    changeover_minutes: float


class ChangeoverTimeOut(BaseModel):
    id: int
    line_id: int
    from_product_id: int
    to_product_id: int
    changeover_minutes: float
    from_product_name: Optional[str] = None
    to_product_name: Optional[str] = None

    class Config:
        from_attributes = True
