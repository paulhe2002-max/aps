from sqlalchemy.orm import Session
from datetime import date, timedelta
from typing import List, Dict, Optional, Tuple
import math

from app.planning.infrastructure.models import NetRequirementModel, RCCPResultModel, PlanningParamModel
from app.orders.infrastructure.models import CustomerOrderModel
from app.inventory.infrastructure.models import InventoryModel
from app.bom.infrastructure.models import ProductModel, BomItemModel
from app.production.infrastructure.models import (
    ProductionLineModel, LineProductModel, WorkingCalendarModel
)


def calculate_latest_start_date(due_date: date, lead_time_days: float) -> date:
    return due_date - timedelta(days=math.ceil(lead_time_days))


def calculate_net_requirements(db: Session) -> List[dict]:
    """Calculate MRP net requirements for all open orders."""
    db.query(NetRequirementModel).delete()

    orders = db.query(CustomerOrderModel).filter(CustomerOrderModel.status == "open").all()
    results = []

    for order in orders:
        product = db.query(ProductModel).filter(ProductModel.id == order.product_id).first()
        if not product:
            continue

        inv = db.query(InventoryModel).filter(InventoryModel.product_id == order.product_id).first()
        actual_stock = inv.actual_stock if inv else 0.0
        in_transit = inv.in_transit if inv else 0.0
        wip = inv.wip if inv else 0.0
        safety_stock = product.safety_stock

        net_req = max(0, order.quantity + safety_stock - actual_stock - in_transit - wip)
        latest_start = calculate_latest_start_date(order.due_date, product.lead_time_days)

        nr = NetRequirementModel(
            product_id=order.product_id,
            order_id=order.id,
            gross_requirement=order.quantity,
            safety_stock=safety_stock,
            actual_stock=actual_stock,
            in_transit=in_transit,
            wip=wip,
            net_requirement=net_req,
            due_date=order.due_date,
            latest_start_date=latest_start,
            is_independent=True,
        )
        db.add(nr)

        # BOM explosion for dependent requirements
        bom_items = db.query(BomItemModel).filter(
            BomItemModel.parent_product_id == order.product_id,
            BomItemModel.is_active == True
        ).all()
        for bom_item in bom_items:
            _explode_dependent(db, bom_item, net_req, order.due_date, order.id, results)

        results.append({
            "order_id": order.id,
            "order_no": order.order_no,
            "product_id": order.product_id,
            "product_name": product.name,
            "product_code": product.code,
            "gross_requirement": order.quantity,
            "safety_stock": safety_stock,
            "actual_stock": actual_stock,
            "in_transit": in_transit,
            "wip": wip,
            "net_requirement": net_req,
            "due_date": str(order.due_date),
            "latest_start_date": str(latest_start),
            "is_independent": True,
        })

    db.commit()
    return results


def _explode_dependent(db: Session, bom_item: BomItemModel, parent_qty: float,
                       parent_due_date: date, parent_order_id: int, results: list):
    child_product = db.query(ProductModel).filter(ProductModel.id == bom_item.child_product_id).first()
    if not child_product:
        return

    gross_req = parent_qty * bom_item.quantity * (1 + bom_item.scrap_rate)
    inv = db.query(InventoryModel).filter(InventoryModel.product_id == child_product.id).first()
    actual_stock = inv.actual_stock if inv else 0.0
    in_transit = inv.in_transit if inv else 0.0
    wip = inv.wip if inv else 0.0
    safety_stock = child_product.safety_stock
    net_req = max(0, gross_req + safety_stock - actual_stock - in_transit - wip)
    latest_start = calculate_latest_start_date(parent_due_date, child_product.lead_time_days)

    nr = NetRequirementModel(
        product_id=child_product.id,
        order_id=None,
        gross_requirement=gross_req,
        safety_stock=safety_stock,
        actual_stock=actual_stock,
        in_transit=in_transit,
        wip=wip,
        net_requirement=net_req,
        due_date=parent_due_date,
        latest_start_date=latest_start,
        is_independent=False,
        parent_order_id=parent_order_id,
    )
    db.add(nr)

    results.append({
        "product_id": child_product.id,
        "product_name": child_product.name,
        "product_code": child_product.code,
        "gross_requirement": gross_req,
        "safety_stock": safety_stock,
        "actual_stock": actual_stock,
        "in_transit": in_transit,
        "wip": wip,
        "net_requirement": net_req,
        "due_date": str(parent_due_date),
        "latest_start_date": str(latest_start),
        "is_independent": False,
        "parent_order_id": parent_order_id,
    })

    # recurse
    child_bom = db.query(BomItemModel).filter(
        BomItemModel.parent_product_id == child_product.id,
        BomItemModel.is_active == True
    ).all()
    for cb in child_bom:
        _explode_dependent(db, cb, net_req, latest_start, parent_order_id, results)


def get_net_requirements(db: Session):
    nrs = db.query(NetRequirementModel).all()
    result = []
    for nr in nrs:
        product = db.query(ProductModel).filter(ProductModel.id == nr.product_id).first()
        result.append({
            "id": nr.id,
            "product_id": nr.product_id,
            "product_name": product.name if product else "",
            "product_code": product.code if product else "",
            "order_id": nr.order_id,
            "gross_requirement": nr.gross_requirement,
            "safety_stock": nr.safety_stock,
            "actual_stock": nr.actual_stock,
            "in_transit": nr.in_transit,
            "wip": nr.wip,
            "net_requirement": nr.net_requirement,
            "due_date": str(nr.due_date),
            "latest_start_date": str(nr.latest_start_date) if nr.latest_start_date else None,
            "is_independent": nr.is_independent,
            "parent_order_id": nr.parent_order_id,
        })
    return result


def get_period_buckets(start_date: date, end_date: date, bucket_type: str) -> List[Tuple[date, date]]:
    buckets = []
    current = start_date
    while current <= end_date:
        if bucket_type == "week":
            period_end = current + timedelta(days=6)
        else:
            # month
            if current.month == 12:
                period_end = date(current.year + 1, 1, 1) - timedelta(days=1)
            else:
                period_end = date(current.year, current.month + 1, 1) - timedelta(days=1)
        period_end = min(period_end, end_date)
        buckets.append((current, period_end))
        current = period_end + timedelta(days=1)
    return buckets


def calculate_rccp(db: Session, start_date: date, end_date: date, bucket_type: str = "week") -> List[dict]:
    """RCCP: Rough Cut Capacity Planning."""
    db.query(RCCPResultModel).delete()

    buckets = get_period_buckets(start_date, end_date, bucket_type)
    lines = db.query(ProductionLineModel).filter(ProductionLineModel.is_active == True).all()
    net_reqs = db.query(NetRequirementModel).filter(
        NetRequirementModel.latest_start_date >= start_date,
        NetRequirementModel.latest_start_date <= end_date,
        NetRequirementModel.net_requirement > 0
    ).all()

    results = []

    for line in lines:
        for bucket_start, bucket_end in buckets:
            available_hours = sum(
                cal.available_hours for cal in db.query(WorkingCalendarModel).filter(
                    WorkingCalendarModel.line_id == line.id,
                    WorkingCalendarModel.work_date >= bucket_start,
                    WorkingCalendarModel.work_date <= bucket_end,
                    WorkingCalendarModel.is_holiday == False
                ).all()
            )

            required_hours = 0.0
            for nr in net_reqs:
                if nr.latest_start_date and bucket_start <= nr.latest_start_date <= bucket_end:
                    lp = db.query(LineProductModel).filter(
                        LineProductModel.line_id == line.id,
                        LineProductModel.product_id == nr.product_id,
                        LineProductModel.is_active == True
                    ).first()
                    if lp:
                        required_hours += (nr.net_requirement * lp.cycle_time_minutes) / 60.0

            utilization = (required_hours / available_hours) if available_hours > 0 else 0.0
            is_overloaded = utilization > 1.0

            rccp = RCCPResultModel(
                period_start=bucket_start,
                period_end=bucket_end,
                bucket_type=bucket_type,
                line_id=line.id,
                required_capacity_hours=required_hours,
                available_capacity_hours=available_hours,
                utilization_rate=utilization,
                is_overloaded=is_overloaded,
            )
            db.add(rccp)

            results.append({
                "period_start": str(bucket_start),
                "period_end": str(bucket_end),
                "bucket_type": bucket_type,
                "line_id": line.id,
                "line_name": line.name,
                "required_capacity_hours": round(required_hours, 2),
                "available_capacity_hours": round(available_hours, 2),
                "utilization_rate": round(utilization * 100, 1),
                "is_overloaded": is_overloaded,
                "adjustment_hours": 0.0,
            })

    db.commit()
    return results


def get_rccp_results(db: Session):
    results = db.query(RCCPResultModel).order_by(
        RCCPResultModel.period_start, RCCPResultModel.line_id
    ).all()
    out = []
    for r in results:
        line = db.query(ProductionLineModel).filter(ProductionLineModel.id == r.line_id).first()
        out.append({
            "id": r.id,
            "period_start": str(r.period_start),
            "period_end": str(r.period_end),
            "bucket_type": r.bucket_type,
            "line_id": r.line_id,
            "line_name": line.name if line else "",
            "required_capacity_hours": round(r.required_capacity_hours, 2),
            "available_capacity_hours": round(r.available_capacity_hours, 2),
            "utilization_rate": round(r.utilization_rate * 100, 1),
            "is_overloaded": r.is_overloaded,
            "adjustment_hours": r.adjustment_hours,
            "adjusted_available": round(r.available_capacity_hours + r.adjustment_hours, 2),
        })
    return out


def adjust_rccp(db: Session, rccp_id: int, adjustment_hours: float):
    rccp = db.query(RCCPResultModel).filter(RCCPResultModel.id == rccp_id).first()
    if not rccp:
        return None
    rccp.adjustment_hours = adjustment_hours
    adjusted = rccp.available_capacity_hours + adjustment_hours
    rccp.utilization_rate = (rccp.required_capacity_hours / adjusted) if adjusted > 0 else 0
    rccp.is_overloaded = rccp.utilization_rate > 1.0
    db.commit()
    db.refresh(rccp)
    return rccp
