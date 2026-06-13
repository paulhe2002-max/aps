from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from app.database import Base


class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    email = Column(String(128), unique=True, index=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    role = Column(String(32), default="planner")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
