from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date
from app.database import get_db
from app.auth.api.router import get_current_active_user
from app.production.api.schemas import (
    ProductionLineCreate, ProductionLineUpdate, ProductionLineOut,
    LineProductCreate, LineProductOut,
    WorkingCalendarCreate, WorkingCalendarOut,
    ChangeoverTimeCreate, ChangeoverTimeOut
)
from app.production.application.service import (
    get_lines, get_line, create_line, update_line,
    get_line_products, create_line_product, delete_line_product,
    get_calendars, create_calendar_entry, bulk_generate_calendar,
    get_changeovers, create_changeover, delete_changeover
)

router = APIRouter(prefix="/production", tags=["production"])


@router.get("/lines", response_model=list[ProductionLineOut])
def list_lines(db: Session = Depends(get_db), user=Depends(get_current_active_user)):
    return get_lines(db)


@router.post("/lines", response_model=ProductionLineOut)
def add_line(data: ProductionLineCreate, db: Session = Depends(get_db), user=Depends(get_current_active_user)):
    return create_line(db, data)


@router.put("/lines/{line_id}", response_model=ProductionLineOut)
def edit_line(line_id: int, data: ProductionLineUpdate, db: Session = Depends(get_db),
              user=Depends(get_current_active_user)):
    line = update_line(db, line_id, data)
    if not line:
        raise HTTPException(404, "Line not found")
    return line


@router.get("/lines/{line_id}/products", response_model=list[LineProductOut])
def list_line_products(line_id: int, db: Session = Depends(get_db), user=Depends(get_current_active_user)):
    return get_line_products(db, line_id)


@router.post("/line-products", response_model=LineProductOut)
def add_line_product(data: LineProductCreate, db: Session = Depends(get_db), user=Depends(get_current_active_user)):
    lp = create_line_product(db, data)
    from app.bom.infrastructure.models import ProductModel
    p = db.query(ProductModel).filter(ProductModel.id == lp.product_id).first()
    if p:
        lp.product_name = p.name
        lp.product_code = p.code
    return lp


@router.delete("/line-products/{lp_id}")
def remove_line_product(lp_id: int, db: Session = Depends(get_db), user=Depends(get_current_active_user)):
    delete_line_product(db, lp_id)
    return {"message": "Deleted"}


@router.get("/lines/{line_id}/calendar", response_model=list[WorkingCalendarOut])
def list_calendar(line_id: int, start_date: Optional[date] = None, end_date: Optional[date] = None,
                  db: Session = Depends(get_db), user=Depends(get_current_active_user)):
    return get_calendars(db, line_id, start_date, end_date)


@router.post("/calendar", response_model=WorkingCalendarOut)
def add_calendar(data: WorkingCalendarCreate, db: Session = Depends(get_db), user=Depends(get_current_active_user)):
    return create_calendar_entry(db, data)


@router.post("/lines/{line_id}/calendar/generate")
def generate_calendar(line_id: int, start_date: date, end_date: date, shifts_per_day: int = 2,
                      hours_per_shift: float = 8.0, db: Session = Depends(get_db),
                      user=Depends(get_current_active_user)):
    return bulk_generate_calendar(db, line_id, start_date, end_date, shifts_per_day, hours_per_shift)


@router.get("/lines/{line_id}/changeovers", response_model=list[ChangeoverTimeOut])
def list_changeovers(line_id: int, db: Session = Depends(get_db), user=Depends(get_current_active_user)):
    return get_changeovers(db, line_id)


@router.post("/changeovers", response_model=ChangeoverTimeOut)
def add_changeover(data: ChangeoverTimeCreate, db: Session = Depends(get_db), user=Depends(get_current_active_user)):
    return create_changeover(db, data)


@router.delete("/changeovers/{co_id}")
def remove_changeover(co_id: int, db: Session = Depends(get_db), user=Depends(get_current_active_user)):
    delete_changeover(db, co_id)
    return {"message": "Deleted"}
