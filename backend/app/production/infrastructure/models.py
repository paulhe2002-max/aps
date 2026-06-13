from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, func, Enum
from app.database import Base


class ProductionLineModel(Base):
    __tablename__ = "production_lines"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(64), unique=True, index=True, nullable=False)
    name = Column(String(128), nullable=False)
    description = Column(String(512), nullable=True)
    capacity_per_shift = Column(Float, default=8.0)
    shifts_per_day = Column(Integer, default=2)
    workers_per_shift = Column(Integer, default=10)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())


class LineProductModel(Base):
    __tablename__ = "line_products"

    id = Column(Integer, primary_key=True, index=True)
    line_id = Column(Integer, nullable=False, index=True)
    product_id = Column(Integer, nullable=False, index=True)
    cycle_time_minutes = Column(Float, nullable=False)
    setup_time_minutes = Column(Float, default=0.0)
    cost_per_unit = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())


class WorkingCalendarModel(Base):
    __tablename__ = "working_calendars"

    id = Column(Integer, primary_key=True, index=True)
    line_id = Column(Integer, nullable=False, index=True)
    work_date = Column(Date, nullable=False, index=True)
    shift_count = Column(Integer, default=2)
    available_hours = Column(Float, default=16.0)
    is_holiday = Column(Boolean, default=False)
    notes = Column(String(256), nullable=True)


class ChangeoverTimeModel(Base):
    __tablename__ = "changeover_times"

    id = Column(Integer, primary_key=True, index=True)
    line_id = Column(Integer, nullable=False, index=True)
    from_product_id = Column(Integer, nullable=False)
    to_product_id = Column(Integer, nullable=False)
    changeover_minutes = Column(Float, default=0.0)
    created_at = Column(DateTime, server_default=func.now())
