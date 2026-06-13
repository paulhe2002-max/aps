from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, func, Enum
from app.database import Base


class ProductModel(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(64), unique=True, index=True, nullable=False)
    name = Column(String(128), nullable=False)
    product_type = Column(Enum("FG", "SFG", "RM"), default="FG")
    unit = Column(String(16), default="PCS")
    lead_time_days = Column(Float, default=1.0)
    safety_stock = Column(Float, default=0.0)
    description = Column(String(512), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class BomItemModel(Base):
    __tablename__ = "bom_items"

    id = Column(Integer, primary_key=True, index=True)
    parent_product_id = Column(Integer, nullable=False, index=True)
    child_product_id = Column(Integer, nullable=False, index=True)
    quantity = Column(Float, nullable=False, default=1.0)
    unit = Column(String(16), default="PCS")
    scrap_rate = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
