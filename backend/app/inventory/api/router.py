from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth.api.router import get_current_active_user
from app.inventory.api.schemas import InventoryCreate, InventoryUpdate, InventoryOut
from app.inventory.application.service import (
    get_all_inventory, get_inventory, upsert_inventory, update_inventory, import_inventory_from_excel
)

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("", response_model=list[InventoryOut])
def list_inventory(db: Session = Depends(get_db), user=Depends(get_current_active_user)):
    return get_all_inventory(db)


@router.post("", response_model=InventoryOut)
def create_or_update_inventory(data: InventoryCreate, db: Session = Depends(get_db),
                                user=Depends(get_current_active_user)):
    return upsert_inventory(db, data)


@router.get("/{product_id}", response_model=InventoryOut)
def read_inventory(product_id: int, db: Session = Depends(get_db), user=Depends(get_current_active_user)):
    item = get_inventory(db, product_id)
    if not item:
        raise HTTPException(404, "Inventory not found")
    return item


@router.put("/{inventory_id}", response_model=InventoryOut)
def edit_inventory(inventory_id: int, data: InventoryUpdate, db: Session = Depends(get_db),
                   user=Depends(get_current_active_user)):
    item = update_inventory(db, inventory_id, data)
    if not item:
        raise HTTPException(404, "Inventory not found")
    return item


@router.post("/import")
async def import_inventory(file: UploadFile = File(...), db: Session = Depends(get_db),
                           user=Depends(get_current_active_user)):
    content = await file.read()
    return import_inventory_from_excel(db, content)
