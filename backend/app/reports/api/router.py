from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import date, timedelta
from app.database import get_db
from app.auth.api.router import get_current_active_user
from app.orders.infrastructure.models import CustomerOrderModel
from app.inventory.infrastructure.models import InventoryModel
from app.bom.infrastructure.models import ProductModel
from app.planning.infrastructure.models import NetRequirementModel, RCCPResultModel
from app.scheduling.infrastructure.models import ScheduleModel, ScheduleItemModel
from app.production.infrastructure.models import ProductionLineModel

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/dashboard")
def dashboard_kpis(db: Session = Depends(get_db), user=Depends(get_current_active_user)):
    total_orders = db.query(CustomerOrderModel).count()
    open_orders = db.query(CustomerOrderModel).filter(CustomerOrderModel.status == "open").count()
    overdue_orders = db.query(CustomerOrderModel).filter(
        CustomerOrderModel.status == "open",
        CustomerOrderModel.due_date < date.today()
    ).count()

    total_products = db.query(ProductModel).filter(ProductModel.is_active == True).count()
    fg_products = db.query(ProductModel).filter(
        ProductModel.product_type == "FG", ProductModel.is_active == True
    ).count()

    net_reqs = db.query(NetRequirementModel).filter(NetRequirementModel.net_requirement > 0).count()

    overloaded = db.query(RCCPResultModel).filter(RCCPResultModel.is_overloaded == True).count()

    active_schedule = db.query(ScheduleModel).filter(ScheduleModel.status == "active").first()

    total_lines = db.query(ProductionLineModel).filter(ProductionLineModel.is_active == True).count()

    return {
        "total_orders": total_orders,
        "open_orders": open_orders,
        "overdue_orders": overdue_orders,
        "total_products": total_products,
        "fg_products": fg_products,
        "pending_net_requirements": net_reqs,
        "overloaded_capacity_periods": overloaded,
        "active_schedule": active_schedule.name if active_schedule else None,
        "active_schedule_on_time_rate": active_schedule.on_time_rate if active_schedule else 0,
        "total_production_lines": total_lines,
    }


@router.get("/inventory-health")
def inventory_health(db: Session = Depends(get_db), user=Depends(get_current_active_user)):
    products = db.query(ProductModel).filter(ProductModel.is_active == True).all()
    result = []
    for product in products:
        inv = db.query(InventoryModel).filter(InventoryModel.product_id == product.id).first()
        actual = inv.actual_stock if inv else 0
        safety = product.safety_stock
        status = "OK" if actual >= safety else ("LOW" if actual > 0 else "STOCKOUT")
        result.append({
            "product_id": product.id,
            "product_code": product.code,
            "product_name": product.name,
            "actual_stock": actual,
            "safety_stock": safety,
            "in_transit": inv.in_transit if inv else 0,
            "wip": inv.wip if inv else 0,
            "status": status,
            "coverage_ratio": round(actual / safety, 2) if safety > 0 else None,
        })
    return result


@router.get("/order-fulfillment")
def order_fulfillment(db: Session = Depends(get_db), user=Depends(get_current_active_user)):
    schedules = db.query(ScheduleModel).order_by(ScheduleModel.created_at.desc()).limit(5).all()
    result = []
    for s in schedules:
        items = db.query(ScheduleItemModel).filter(ScheduleItemModel.schedule_id == s.id).all()
        total = len(items)
        on_time = sum(1 for i in items if i.is_on_time)
        result.append({
            "schedule_id": s.id,
            "schedule_name": s.name,
            "algorithm": s.algorithm,
            "total_jobs": total,
            "on_time_jobs": on_time,
            "on_time_rate": round(on_time / total * 100, 1) if total > 0 else 0,
            "total_cost": s.total_cost,
            "utilization_rate": s.utilization_rate,
            "makespan_days": s.makespan_days,
            "status": s.status,
        })
    return result


@router.get("/capacity-utilization")
def capacity_utilization(db: Session = Depends(get_db), user=Depends(get_current_active_user)):
    rccp = db.query(RCCPResultModel).order_by(RCCPResultModel.period_start).all()
    lines = {l.id: l.name for l in db.query(ProductionLineModel).all()}
    result = []
    for r in rccp:
        adjusted_avail = r.available_capacity_hours + r.adjustment_hours
        util = (r.required_capacity_hours / adjusted_avail * 100) if adjusted_avail > 0 else 0
        result.append({
            "period": str(r.period_start),
            "period_end": str(r.period_end),
            "line_name": lines.get(r.line_id, f"Line {r.line_id}"),
            "required_hours": round(r.required_capacity_hours, 2),
            "available_hours": round(adjusted_avail, 2),
            "utilization_pct": round(util, 1),
            "is_overloaded": util > 100,
        })
    return result


@router.get("/wip-analysis")
def wip_analysis(db: Session = Depends(get_db), user=Depends(get_current_active_user)):
    items = db.query(InventoryModel).filter(InventoryModel.wip > 0).all()
    result = []
    for item in items:
        product = db.query(ProductModel).filter(ProductModel.id == item.product_id).first()
        result.append({
            "product_code": product.code if product else "",
            "product_name": product.name if product else "",
            "wip_quantity": item.wip,
            "actual_stock": item.actual_stock,
            "in_transit": item.in_transit,
        })
    return result
