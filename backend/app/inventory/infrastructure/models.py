from sqlalchemy import Column, Integer, Float, Date, DateTime, String, func
from app.database import Base


class InventoryModel(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, nullable=False, index=True, unique=True)
    actual_stock = Column(Float, default=0.0)
    in_transit = Column(Float, default=0.0)
    wip = Column(Float, default=0.0)
    last_updated = Column(Date, nullable=True)
    notes = Column(String(512), nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
