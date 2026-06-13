from sqlalchemy.orm import Session
from app.bom.infrastructure.models import ProductModel, BomItemModel
from app.bom.api.schemas import ProductCreate, ProductUpdate, BomItemCreate
from typing import List, Dict, Optional


def get_products(db: Session, product_type: Optional[str] = None):
    q = db.query(ProductModel).filter(ProductModel.is_active == True)
    if product_type:
        q = q.filter(ProductModel.product_type == product_type)
    return q.all()


def get_product(db: Session, product_id: int):
    return db.query(ProductModel).filter(ProductModel.id == product_id).first()


def create_product(db: Session, data: ProductCreate):
    product = ProductModel(**data.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def update_product(db: Session, product_id: int, data: ProductUpdate):
    product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
    if not product:
        return None
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(product, k, v)
    db.commit()
    db.refresh(product)
    return product


def delete_product(db: Session, product_id: int):
    product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
    if product:
        product.is_active = False
        db.commit()
    return product


def get_bom_items(db: Session, parent_product_id: int):
    items = db.query(BomItemModel).filter(
        BomItemModel.parent_product_id == parent_product_id,
        BomItemModel.is_active == True
    ).all()
    for item in items:
        item.child_product = get_product(db, item.child_product_id)
    return items


def create_bom_item(db: Session, data: BomItemCreate):
    item = BomItemModel(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def delete_bom_item(db: Session, item_id: int):
    item = db.query(BomItemModel).filter(BomItemModel.id == item_id).first()
    if item:
        item.is_active = False
        db.commit()
    return item


def get_bom_tree(db: Session, product_id: int, quantity: float = 1.0, scrap_rate: float = 0.0, visited=None) -> dict:
    if visited is None:
        visited = set()
    if product_id in visited:
        return None
    visited.add(product_id)
    product = get_product(db, product_id)
    if not product:
        return None
    children = []
    bom_items = db.query(BomItemModel).filter(
        BomItemModel.parent_product_id == product_id,
        BomItemModel.is_active == True
    ).all()
    for item in bom_items:
        child_tree = get_bom_tree(db, item.child_product_id, item.quantity * quantity, item.scrap_rate, visited.copy())
        if child_tree:
            children.append(child_tree)
    return {
        "product": product,
        "quantity": quantity,
        "scrap_rate": scrap_rate,
        "children": children
    }


def explode_bom(db: Session, product_id: int, quantity: float) -> Dict[int, float]:
    """Explode BOM to get all component requirements (flat)."""
    result = {}
    items = db.query(BomItemModel).filter(
        BomItemModel.parent_product_id == product_id,
        BomItemModel.is_active == True
    ).all()
    for item in items:
        req_qty = quantity * item.quantity * (1 + item.scrap_rate)
        child_id = item.child_product_id
        result[child_id] = result.get(child_id, 0) + req_qty
        child_reqs = explode_bom(db, child_id, req_qty)
        for cid, cqty in child_reqs.items():
            result[cid] = result.get(cid, 0) + cqty
    return result
