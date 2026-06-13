from sqlalchemy.orm import Session
from app.inventory.infrastructure.models import InventoryModel
from app.inventory.api.schemas import InventoryCreate, InventoryUpdate
from app.bom.infrastructure.models import ProductModel
from typing import Optional
import io
import pandas as pd


def get_all_inventory(db: Session):
    items = db.query(InventoryModel).all()
    for item in items:
        product = db.query(ProductModel).filter(ProductModel.id == item.product_id).first()
        if product:
            item.product_name = product.name
            item.product_code = product.code
            item.safety_stock = product.safety_stock
    return items


def get_inventory(db: Session, product_id: int) -> Optional[InventoryModel]:
    item = db.query(InventoryModel).filter(InventoryModel.product_id == product_id).first()
    if item:
        product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
        if product:
            item.product_name = product.name
            item.product_code = product.code
            item.safety_stock = product.safety_stock
    return item


def upsert_inventory(db: Session, data: InventoryCreate) -> InventoryModel:
    item = db.query(InventoryModel).filter(InventoryModel.product_id == data.product_id).first()
    if item:
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(item, k, v)
    else:
        item = InventoryModel(**data.model_dump())
        db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_inventory(db: Session, inventory_id: int, data: InventoryUpdate):
    item = db.query(InventoryModel).filter(InventoryModel.id == inventory_id).first()
    if not item:
        return None
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(item, k, v)
    db.commit()
    db.refresh(item)
    return item


def import_inventory_from_excel(db: Session, file_bytes: bytes) -> dict:
    df = pd.read_excel(io.BytesIO(file_bytes))
    df.columns = [c.strip().lower() for c in df.columns]
    updated, skipped = 0, 0
    for _, row in df.iterrows():
        product = db.query(ProductModel).filter(ProductModel.code == str(row.get("product_code", ""))).first()
        if not product:
            skipped += 1
            continue
        item = db.query(InventoryModel).filter(InventoryModel.product_id == product.id).first()
        if not item:
            item = InventoryModel(product_id=product.id)
            db.add(item)
        item.actual_stock = float(row.get("actual_stock", 0))
        item.in_transit = float(row.get("in_transit", 0))
        item.wip = float(row.get("wip", 0))
        updated += 1
    db.commit()
    return {"updated": updated, "skipped": skipped}
