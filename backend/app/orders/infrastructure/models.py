from sqlalchemy import Column, Integer, String, Float, Date, DateTime, func, Enum
from app.database import Base


class CustomerOrderModel(Base):
    __tablename__ = "customer_orders"

    id = Column(Integer, primary_key=True, index=True)
    order_no = Column(String(64), unique=True, index=True, nullable=False)
    product_id = Column(Integer, nullable=False, index=True)
    quantity = Column(Float, nullable=False)
    due_date = Column(Date, nullable=False)
    priority = Column(Integer, default=5)
    customer_name = Column(String(128), nullable=True)
    status = Column(Enum("open", "in_progress", "completed", "cancelled"), default="open")
    notes = Column(String(512), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
