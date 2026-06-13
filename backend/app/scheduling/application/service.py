from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from app.scheduling.infrastructure.models import ScheduleModel, ScheduleItemModel
from app.scheduling.domain.algorithms import Job, Machine, ALGORITHM_MAP, compute_kpis
from app.planning.infrastructure.models import NetRequirementModel
from app.orders.infrastructure.models import CustomerOrderModel
from app.bom.infrastructure.models import ProductModel
from app.production.infrastructure.models import (
    ProductionLineModel, LineProductModel, WorkingCalendarModel, ChangeoverTimeModel
)


def build_jobs_and_machines(db: Session) -> tuple:
    """Build Job and Machine objects from database for scheduling."""
    net_reqs = db.query(NetRequirementModel).filter(
        NetRequirementModel.is_independent == True,
        NetRequirementModel.net_requirement > 0
    ).all()

    jobs = []
    for nr in net_reqs:
        product = db.query(ProductModel).filter(ProductModel.id == nr.product_id).first()
        if not product:
            continue
        order = db.query(CustomerOrderModel).filter(CustomerOrderModel.id == nr.order_id).first() if nr.order_id else None
        order_no = order.order_no if order else f"AUTO-{nr.id}"
        priority = order.priority if order else 5

        # Find best cycle time (first available line)
        lp = db.query(LineProductModel).filter(
            LineProductModel.product_id == nr.product_id,
            LineProductModel.is_active == True
        ).first()
        cycle_time = lp.cycle_time_minutes if lp else 1.0
        setup_time = lp.setup_time_minutes if lp else 0.0
        cost_per_unit = lp.cost_per_unit if lp else 0.0

        due_date = datetime.combine(nr.due_date, datetime.min.time()).replace(hour=23, minute=59)
        jobs.append(Job(
            order_id=nr.order_id or nr.id,
            product_id=nr.product_id,
            quantity=nr.net_requirement,
            due_date=due_date,
            priority=priority,
            cycle_time_minutes=cycle_time,
            setup_time=setup_time,
            cost_per_unit=cost_per_unit,
            product_name=product.name,
            order_no=order_no,
        ))

    lines = db.query(ProductionLineModel).filter(ProductionLineModel.is_active == True).all()
    machines = []
    for line in lines:
        machines.append(Machine(
            line_id=line.id,
            line_name=line.name,
            available_hours_per_day=line.capacity_per_shift * line.shifts_per_day,
            shifts_per_day=line.shifts_per_day,
            workers_per_shift=line.workers_per_shift,
        ))

    # Build changeover matrix
    changeover_matrix = {}
    changeovers = db.query(ChangeoverTimeModel).all()
    for co in changeovers:
        changeover_matrix[(co.line_id, co.from_product_id, co.to_product_id)] = co.changeover_minutes

    return jobs, machines, changeover_matrix


def run_scheduling(db: Session, algorithm: str, name: str, objective: str = "on_time",
                   start_dt: datetime = None, params: dict = None) -> dict:
    if start_dt is None:
        start_dt = datetime.now().replace(hour=6, minute=0, second=0, microsecond=0)

    jobs, machines, changeover_matrix = build_jobs_and_machines(db)
    if not jobs or not machines:
        return {"error": "No jobs or machines available. Run MRP first and ensure production lines exist."}

    algo_fn = ALGORITHM_MAP.get(algorithm)
    if not algo_fn:
        return {"error": f"Unknown algorithm: {algorithm}"}

    extra_params = params or {}
    result = algo_fn(jobs, machines, start_dt, changeover_matrix, **extra_params)

    schedule = ScheduleModel(
        name=name,
        algorithm=algorithm,
        status="draft",
        objective=objective,
        total_cost=result.kpis.get("total_cost", 0),
        on_time_rate=result.kpis.get("on_time_rate", 0),
        utilization_rate=result.kpis.get("utilization_rate", 0),
        makespan_days=result.kpis.get("makespan_hours", 0) / 24.0,
        params=params,
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)

    for item in result.items:
        si = ScheduleItemModel(
            schedule_id=schedule.id,
            order_id=item.get("order_id"),
            product_id=item["product_id"],
            line_id=item["line_id"],
            sequence=item["sequence"],
            planned_quantity=item["planned_quantity"],
            start_datetime=item["start_datetime"],
            end_datetime=item["end_datetime"],
            setup_time_minutes=item.get("setup_time_minutes", 0),
            changeover_minutes=item.get("changeover_minutes", 0),
            cycle_time_minutes=item.get("cycle_time_minutes", 0),
            cost=item.get("cost", 0),
            is_on_time=item.get("is_on_time", True),
        )
        db.add(si)
    db.commit()

    return {
        "schedule_id": schedule.id,
        "algorithm": algorithm,
        "kpis": result.kpis,
        "items": result.items,
        "steps": result.steps,
    }


def get_schedules(db: Session):
    return db.query(ScheduleModel).order_by(ScheduleModel.created_at.desc()).all()


def get_schedule(db: Session, schedule_id: int):
    return db.query(ScheduleModel).filter(ScheduleModel.id == schedule_id).first()


def get_schedule_items(db: Session, schedule_id: int):
    items = db.query(ScheduleItemModel).filter(ScheduleItemModel.schedule_id == schedule_id).all()
    result = []
    for item in items:
        product = db.query(ProductModel).filter(ProductModel.id == item.product_id).first()
        line = db.query(ProductionLineModel).filter(ProductionLineModel.id == item.line_id).first()
        order = db.query(CustomerOrderModel).filter(CustomerOrderModel.id == item.order_id).first() if item.order_id else None
        result.append({
            "id": item.id,
            "schedule_id": item.schedule_id,
            "order_id": item.order_id,
            "order_no": order.order_no if order else "",
            "product_id": item.product_id,
            "product_name": product.name if product else "",
            "product_code": product.code if product else "",
            "line_id": item.line_id,
            "line_name": line.name if line else "",
            "sequence": item.sequence,
            "planned_quantity": item.planned_quantity,
            "start_datetime": item.start_datetime,
            "end_datetime": item.end_datetime,
            "setup_time_minutes": item.setup_time_minutes,
            "changeover_minutes": item.changeover_minutes,
            "cycle_time_minutes": item.cycle_time_minutes,
            "cost": item.cost,
            "is_on_time": item.is_on_time,
        })
    return result


def approve_schedule(db: Session, schedule_id: int):
    # Deactivate all other active schedules
    db.query(ScheduleModel).filter(ScheduleModel.status == "active").update({"status": "draft"})
    schedule = db.query(ScheduleModel).filter(ScheduleModel.id == schedule_id).first()
    if schedule:
        schedule.status = "active"
        db.commit()
    return schedule


def compare_schedules(db: Session, schedule_ids: List[int]) -> List[dict]:
    result = []
    for sid in schedule_ids:
        s = db.query(ScheduleModel).filter(ScheduleModel.id == sid).first()
        if s:
            result.append({
                "schedule_id": s.id,
                "name": s.name,
                "algorithm": s.algorithm,
                "on_time_rate": s.on_time_rate,
                "total_cost": s.total_cost,
                "utilization_rate": s.utilization_rate,
                "makespan_days": s.makespan_days,
                "status": s.status,
            })
    return result


def run_simulation_step(algorithm: str, jobs: List[Job], machines: List[Machine],
                         changeover_matrix: dict, start_dt: datetime, step_idx: int) -> dict:
    """Return simulation step detail for a given algorithm."""
    algo_fn = ALGORITHM_MAP.get(algorithm)
    if not algo_fn:
        return {"error": "Unknown algorithm"}
    result = algo_fn(jobs, machines, start_dt, changeover_matrix)
    if step_idx < len(result.steps):
        return {"step": result.steps[step_idx], "total_steps": len(result.steps)}
    return {"step": None, "total_steps": len(result.steps), "message": "No more steps"}
