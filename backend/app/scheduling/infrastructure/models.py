from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON, func, Enum
from app.database import Base


class ScheduleModel(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    algorithm = Column(String(64), nullable=False)
    status = Column(Enum("draft", "approved", "active"), default="draft")
    objective = Column(String(256), nullable=True)
    total_cost = Column(Float, default=0.0)
    on_time_rate = Column(Float, default=0.0)
    utilization_rate = Column(Float, default=0.0)
    makespan_days = Column(Float, default=0.0)
    params = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class ScheduleItemModel(Base):
    __tablename__ = "schedule_items"

    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, nullable=False, index=True)
    order_id = Column(Integer, nullable=True)
    product_id = Column(Integer, nullable=False)
    line_id = Column(Integer, nullable=False)
    sequence = Column(Integer, default=0)
    planned_quantity = Column(Float, nullable=False)
    start_datetime = Column(String(32), nullable=False)
    end_datetime = Column(String(32), nullable=False)
    setup_time_minutes = Column(Float, default=0.0)
    changeover_minutes = Column(Float, default=0.0)
    cycle_time_minutes = Column(Float, default=0.0)
    cost = Column(Float, default=0.0)
    is_on_time = Column(Boolean, default=True)
    notes = Column(String(256), nullable=True)
