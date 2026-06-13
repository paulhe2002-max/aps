from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Boolean, func, Enum
from app.database import Base


class PlanningParamModel(Base):
    __tablename__ = "planning_params"

    id = Column(Integer, primary_key=True, index=True)
    bucket_type = Column(Enum("week", "month"), default="week")
    horizon_days = Column(Integer, default=90)
    rccp_start_date = Column(Date, nullable=True)
    rccp_end_date = Column(Date, nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class NetRequirementModel(Base):
    __tablename__ = "net_requirements"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, nullable=False, index=True)
    order_id = Column(Integer, nullable=True)
    gross_requirement = Column(Float, default=0.0)
    safety_stock = Column(Float, default=0.0)
    actual_stock = Column(Float, default=0.0)
    in_transit = Column(Float, default=0.0)
    wip = Column(Float, default=0.0)
    net_requirement = Column(Float, default=0.0)
    due_date = Column(Date, nullable=False)
    latest_start_date = Column(Date, nullable=True)
    is_independent = Column(Boolean, default=True)
    parent_order_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class RCCPResultModel(Base):
    __tablename__ = "rccp_results"

    id = Column(Integer, primary_key=True, index=True)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    bucket_type = Column(String(16), default="week")
    line_id = Column(Integer, nullable=False, index=True)
    product_id = Column(Integer, nullable=True)
    required_capacity_hours = Column(Float, default=0.0)
    available_capacity_hours = Column(Float, default=0.0)
    utilization_rate = Column(Float, default=0.0)
    is_overloaded = Column(Boolean, default=False)
    adjustment_hours = Column(Float, default=0.0)
    created_at = Column(DateTime, server_default=func.now())
