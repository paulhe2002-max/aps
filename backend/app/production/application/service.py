from sqlalchemy.orm import Session
from datetime import date, timedelta
from app.production.infrastructure.models import (
    ProductionLineModel, LineProductModel, WorkingCalendarModel, ChangeoverTimeModel
)
from app.production.api.schemas import (
    ProductionLineCreate, ProductionLineUpdate, LineProductCreate,
    WorkingCalendarCreate, ChangeoverTimeCreate
)
from app.bom.infrastructure.models import ProductModel
from typing import Optional, List


def get_lines(db: Session):
    return db.query(ProductionLineModel).filter(ProductionLineModel.is_active == True).all()


def get_line(db: Session, line_id: int):
    return db.query(ProductionLineModel).filter(ProductionLineModel.id == line_id).first()


def create_line(db: Session, data: ProductionLineCreate):
    line = ProductionLineModel(**data.model_dump())
    db.add(line)
    db.commit()
    db.refresh(line)
    return line


def update_line(db: Session, line_id: int, data: ProductionLineUpdate):
    line = db.query(ProductionLineModel).filter(ProductionLineModel.id == line_id).first()
    if not line:
        return None
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(line, k, v)
    db.commit()
    db.refresh(line)
    return line


def get_line_products(db: Session, line_id: int):
    items = db.query(LineProductModel).filter(
        LineProductModel.line_id == line_id, LineProductModel.is_active == True
    ).all()
    for item in items:
        product = db.query(ProductModel).filter(ProductModel.id == item.product_id).first()
        if product:
            item.product_name = product.name
            item.product_code = product.code
    return items


def create_line_product(db: Session, data: LineProductCreate):
    lp = LineProductModel(**data.model_dump())
    db.add(lp)
    db.commit()
    db.refresh(lp)
    return lp


def delete_line_product(db: Session, lp_id: int):
    lp = db.query(LineProductModel).filter(LineProductModel.id == lp_id).first()
    if lp:
        lp.is_active = False
        db.commit()


def get_calendars(db: Session, line_id: int, start_date: Optional[date] = None, end_date: Optional[date] = None):
    q = db.query(WorkingCalendarModel).filter(WorkingCalendarModel.line_id == line_id)
    if start_date:
        q = q.filter(WorkingCalendarModel.work_date >= start_date)
    if end_date:
        q = q.filter(WorkingCalendarModel.work_date <= end_date)
    return q.order_by(WorkingCalendarModel.work_date).all()


def create_calendar_entry(db: Session, data: WorkingCalendarCreate):
    cal = WorkingCalendarModel(**data.model_dump())
    db.add(cal)
    db.commit()
    db.refresh(cal)
    return cal


def bulk_generate_calendar(db: Session, line_id: int, start_date: date, end_date: date,
                            shifts_per_day: int = 2, hours_per_shift: float = 8.0, holidays: List[date] = None):
    if holidays is None:
        holidays = []
    current = start_date
    created = 0
    while current <= end_date:
        existing = db.query(WorkingCalendarModel).filter(
            WorkingCalendarModel.line_id == line_id,
            WorkingCalendarModel.work_date == current
        ).first()
        if not existing:
            is_holiday = current in holidays or current.weekday() >= 5
            cal = WorkingCalendarModel(
                line_id=line_id,
                work_date=current,
                shift_count=0 if is_holiday else shifts_per_day,
                available_hours=0.0 if is_holiday else shifts_per_day * hours_per_shift,
                is_holiday=is_holiday
            )
            db.add(cal)
            created += 1
        current += timedelta(days=1)
    db.commit()
    return {"created": created}


def get_changeovers(db: Session, line_id: int):
    items = db.query(ChangeoverTimeModel).filter(ChangeoverTimeModel.line_id == line_id).all()
    for item in items:
        fp = db.query(ProductModel).filter(ProductModel.id == item.from_product_id).first()
        tp = db.query(ProductModel).filter(ProductModel.id == item.to_product_id).first()
        item.from_product_name = fp.name if fp else None
        item.to_product_name = tp.name if tp else None
    return items


def create_changeover(db: Session, data: ChangeoverTimeCreate):
    co = ChangeoverTimeModel(**data.model_dump())
    db.add(co)
    db.commit()
    db.refresh(co)
    return co


def delete_changeover(db: Session, co_id: int):
    co = db.query(ChangeoverTimeModel).filter(ChangeoverTimeModel.id == co_id).first()
    if co:
        db.delete(co)
        db.commit()


def get_changeover_time(db: Session, line_id: int, from_product_id: int, to_product_id: int) -> float:
    co = db.query(ChangeoverTimeModel).filter(
        ChangeoverTimeModel.line_id == line_id,
        ChangeoverTimeModel.from_product_id == from_product_id,
        ChangeoverTimeModel.to_product_id == to_product_id
    ).first()
    return co.changeover_minutes if co else 0.0
