from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.auth.api.router import get_current_active_user
from app.orders.api.schemas import CustomerOrderCreate, CustomerOrderUpdate, CustomerOrderOut
from app.orders.application.service import (
    get_orders, get_order, create_order, update_order, delete_order, import_orders_from_excel
)

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("", response_model=list[CustomerOrderOut])
def list_orders(status: Optional[str] = None, product_id: Optional[int] = None,
                db: Session = Depends(get_db), user=Depends(get_current_active_user)):
    return get_orders(db, status, product_id)


@router.post("", response_model=CustomerOrderOut)
def add_order(data: CustomerOrderCreate, db: Session = Depends(get_db), user=Depends(get_current_active_user)):
    return create_order(db, data)


@router.get("/{order_id}", response_model=CustomerOrderOut)
def read_order(order_id: int, db: Session = Depends(get_db), user=Depends(get_current_active_user)):
    o = get_order(db, order_id)
    if not o:
        raise HTTPException(404, "Order not found")
    return o


@router.put("/{order_id}", response_model=CustomerOrderOut)
def edit_order(order_id: int, data: CustomerOrderUpdate, db: Session = Depends(get_db),
               user=Depends(get_current_active_user)):
    o = update_order(db, order_id, data)
    if not o:
        raise HTTPException(404, "Order not found")
    return o


@router.delete("/{order_id}")
def remove_order(order_id: int, db: Session = Depends(get_db), user=Depends(get_current_active_user)):
    delete_order(db, order_id)
    return {"message": "Deleted"}


@router.post("/import")
async def import_orders(file: UploadFile = File(...), db: Session = Depends(get_db),
                        user=Depends(get_current_active_user)):
    content = await file.read()
    result = import_orders_from_excel(db, content)
    return result
