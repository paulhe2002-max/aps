from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    from app.auth.infrastructure.models import UserModel
    from app.orders.infrastructure.models import CustomerOrderModel
    from app.inventory.infrastructure.models import InventoryModel
    from app.bom.infrastructure.models import ProductModel, BomItemModel
    from app.production.infrastructure.models import (
        ProductionLineModel, LineProductModel, WorkingCalendarModel, ChangeoverTimeModel
    )
    from app.planning.infrastructure.models import (
        PlanningParamModel, NetRequirementModel, RCCPResultModel
    )
    from app.scheduling.infrastructure.models import ScheduleModel, ScheduleItemModel
    Base.metadata.create_all(bind=engine)
