from sqlalchemy.orm import Session
from app.orders.infrastructure.models import CustomerOrderModel
from app.orders.api.schemas import CustomerOrderCreate, CustomerOrderUpdate
from app.bom.infrastructure.models import ProductModel
from typing import Optional
import io
import pandas as pd


def get_orders(db: Session, status: Optional[str] = None, product_id: Optional[int] = None):
    q = db.query(CustomerOrderModel)
    if status:
        q = q.filter(CustomerOrderModel.status == status)
    if product_id:
        q = q.filter(CustomerOrderModel.product_id == product_id)
    orders = q.order_by(CustomerOrderModel.due_date).all()
    for order in orders:
        product = db.query(ProductModel).filter(ProductModel.id == order.product_id).first()
        if product:
            order.product_name = product.name
            order.product_code = product.code
    return orders


def get_order(db: Session, order_id: int):
    order = db.query(CustomerOrderModel).filter(CustomerOrderModel.id == order_id).first()
    if order:
        product = db.query(ProductModel).filter(ProductModel.id == order.product_id).first()
        if product:
            order.product_name = product.name
            order.product_code = product.code
    return order


def create_order(db: Session, data: CustomerOrderCreate):
    order = CustomerOrderModel(**data.model_dump())
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def update_order(db: Session, order_id: int, data: CustomerOrderUpdate):
    order = db.query(CustomerOrderModel).filter(CustomerOrderModel.id == order_id).first()
    if not order:
        return None
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(order, k, v)
    db.commit()
    db.refresh(order)
    return order


def delete_order(db: Session, order_id: int):
    order = db.query(CustomerOrderModel).filter(CustomerOrderModel.id == order_id).first()
    if order:
        db.delete(order)
        db.commit()
    return order


def import_orders_from_excel(db: Session, file_bytes: bytes) -> dict:
    df = pd.read_excel(io.BytesIO(file_bytes))
    df.columns = [c.strip().lower() for c in df.columns]
    required = {"order_no", "product_code", "quantity", "due_date"}
    if not required.issubset(set(df.columns)):
        return {"error": f"Missing columns. Required: {required}"}
    created, skipped = 0, 0
    for _, row in df.iterrows():
        product = db.query(ProductModel).filter(ProductModel.code == str(row["product_code"])).first()
        if not product:
            skipped += 1
            continue
        existing = db.query(CustomerOrderModel).filter(
            CustomerOrderModel.order_no == str(row["order_no"])
        ).first()
        if existing:
            skipped += 1
            continue
        order = CustomerOrderModel(
            order_no=str(row["order_no"]),
            product_id=product.id,
            quantity=float(row["quantity"]),
            due_date=pd.to_datetime(row["due_date"]).date(),
            priority=int(row.get("priority", 5)),
            customer_name=str(row.get("customer_name", "")),
            status="open",
        )
        db.add(order)
        created += 1
    db.commit()
    return {"created": created, "skipped": skipped}
