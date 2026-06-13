from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from app.database import get_db
from app.auth.api.router import get_current_active_user
from app.scheduling.application.service import (
    run_scheduling, get_schedules, get_schedule, get_schedule_items,
    approve_schedule, compare_schedules, build_jobs_and_machines
)

router = APIRouter(prefix="/scheduling", tags=["scheduling"])


@router.post("/run")
def run_schedule(
    algorithm: str = "EDD",
    name: str = "New Schedule",
    objective: str = "on_time",
    start_date: Optional[str] = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_active_user)
):
    start_dt = None
    if start_date:
        start_dt = datetime.fromisoformat(start_date)
    result = run_scheduling(db, algorithm, name, objective, start_dt)
    return result


@router.get("/schedules")
def list_schedules(db: Session = Depends(get_db), user=Depends(get_current_active_user)):
    schedules = get_schedules(db)
    return [
        {
            "id": s.id, "name": s.name, "algorithm": s.algorithm, "status": s.status,
            "objective": s.objective, "total_cost": s.total_cost, "on_time_rate": s.on_time_rate,
            "utilization_rate": s.utilization_rate, "makespan_days": s.makespan_days,
            "created_at": str(s.created_at),
        }
        for s in schedules
    ]


@router.get("/schedules/{schedule_id}")
def read_schedule(schedule_id: int, db: Session = Depends(get_db), user=Depends(get_current_active_user)):
    s = get_schedule(db, schedule_id)
    if not s:
        raise HTTPException(404, "Schedule not found")
    items = get_schedule_items(db, schedule_id)
    return {
        "id": s.id, "name": s.name, "algorithm": s.algorithm, "status": s.status,
        "on_time_rate": s.on_time_rate, "total_cost": s.total_cost,
        "utilization_rate": s.utilization_rate, "makespan_days": s.makespan_days,
        "items": items
    }


@router.post("/schedules/{schedule_id}/approve")
def approve(schedule_id: int, db: Session = Depends(get_db), user=Depends(get_current_active_user)):
    s = approve_schedule(db, schedule_id)
    if not s:
        raise HTTPException(404, "Schedule not found")
    return {"message": "Schedule approved", "id": s.id}


@router.post("/compare")
def compare(schedule_ids: List[int], db: Session = Depends(get_db), user=Depends(get_current_active_user)):
    return compare_schedules(db, schedule_ids)


@router.get("/simulation/{algorithm}")
def simulate_algorithm(algorithm: str, db: Session = Depends(get_db), user=Depends(get_current_active_user)):
    """Run algorithm and return all simulation steps."""
    from app.scheduling.domain.algorithms import ALGORITHM_MAP
    jobs, machines, changeover_matrix = build_jobs_and_machines(db)
    if not jobs or not machines:
        return {"error": "No data. Run MRP first."}
    algo_fn = ALGORITHM_MAP.get(algorithm)
    if not algo_fn:
        raise HTTPException(400, f"Unknown algorithm: {algorithm}")
    start_dt = datetime.now().replace(hour=6, minute=0, second=0, microsecond=0)
    result = algo_fn(jobs, machines, start_dt, changeover_matrix)
    return {
        "algorithm": algorithm,
        "steps": result.steps,
        "kpis": result.kpis,
        "items": result.items,
        "total_steps": len(result.steps),
    }
