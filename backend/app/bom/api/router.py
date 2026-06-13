from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.auth.api.router import get_current_active_user
from app.bom.api.schemas import ProductCreate, ProductUpdate, ProductOut, BomItemCreate, BomItemOut
from app.bom.application.service import (
    get_products, get_product, create_product, update_product, delete_product,
    get_bom_items, create_bom_item, delete_bom_item, get_bom_tree
)

router = APIRouter(prefix="/bom", tags=["bom"])


@router.get("/products", response_model=list[ProductOut])
def list_products(product_type: Optional[str] = None, db: Session = Depends(get_db),
                  user=Depends(get_current_active_user)):
    return get_products(db, product_type)


@router.post("/products", response_model=ProductOut)
def add_product(data: ProductCreate, db: Session = Depends(get_db), user=Depends(get_current_active_user)):
    return create_product(db, data)


@router.get("/products/{product_id}", response_model=ProductOut)
def read_product(product_id: int, db: Session = Depends(get_db), user=Depends(get_current_active_user)):
    p = get_product(db, product_id)
    if not p:
        raise HTTPException(404, "Product not found")
    return p


@router.put("/products/{product_id}", response_model=ProductOut)
def edit_product(product_id: int, data: ProductUpdate, db: Session = Depends(get_db),
                 user=Depends(get_current_active_user)):
    p = update_product(db, product_id, data)
    if not p:
        raise HTTPException(404, "Product not found")
    return p


@router.delete("/products/{product_id}")
def remove_product(product_id: int, db: Session = Depends(get_db), user=Depends(get_current_active_user)):
    delete_product(db, product_id)
    return {"message": "Deleted"}


@router.get("/products/{product_id}/bom", response_model=list[BomItemOut])
def list_bom(product_id: int, db: Session = Depends(get_db), user=Depends(get_current_active_user)):
    return get_bom_items(db, product_id)


@router.post("/bom-items", response_model=BomItemOut)
def add_bom_item(data: BomItemCreate, db: Session = Depends(get_db), user=Depends(get_current_active_user)):
    item = create_bom_item(db, data)
    item.child_product = get_product(db, item.child_product_id)
    return item


@router.delete("/bom-items/{item_id}")
def remove_bom_item(item_id: int, db: Session = Depends(get_db), user=Depends(get_current_active_user)):
    delete_bom_item(db, item_id)
    return {"message": "Deleted"}


@router.get("/products/{product_id}/tree")
def bom_tree(product_id: int, db: Session = Depends(get_db), user=Depends(get_current_active_user)):
    tree = get_bom_tree(db, product_id)
    if not tree:
        raise HTTPException(404, "Product not found")
    return tree
