from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import date
from app.database import get_db
from app.auth.api.router import get_current_active_user
from app.planning.application.service import (
    calculate_net_requirements, get_net_requirements,
    calculate_rccp, get_rccp_results, adjust_rccp
)

router = APIRouter(prefix="/planning", tags=["planning"])


@router.post("/mrp/calculate")
def run_mrp(db: Session = Depends(get_db), user=Depends(get_current_active_user)):
    results = calculate_net_requirements(db)
    return {"count": len(results), "results": results}


@router.get("/mrp/net-requirements")
def list_net_requirements(db: Session = Depends(get_db), user=Depends(get_current_active_user)):
    return get_net_requirements(db)


@router.post("/rccp/calculate")
def run_rccp(start_date: date, end_date: date, bucket_type: str = "week",
             db: Session = Depends(get_db), user=Depends(get_current_active_user)):
    results = calculate_rccp(db, start_date, end_date, bucket_type)
    return {"count": len(results), "results": results}


@router.get("/rccp/results")
def list_rccp(db: Session = Depends(get_db), user=Depends(get_current_active_user)):
    return get_rccp_results(db)


@router.put("/rccp/{rccp_id}/adjust")
def adjust_capacity(rccp_id: int, adjustment_hours: float,
                    db: Session = Depends(get_db), user=Depends(get_current_active_user)):
    r = adjust_rccp(db, rccp_id, adjustment_hours)
    if not r:
        from fastapi import HTTPException
        raise HTTPException(404, "RCCP record not found")
    return {"id": r.id, "adjustment_hours": r.adjustment_hours, "utilization_rate": round(r.utilization_rate * 100, 1)}
