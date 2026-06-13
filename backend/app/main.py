from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import create_tables
from app.auth.api.router import router as auth_router
from app.bom.api.router import router as bom_router
from app.orders.api.router import router as orders_router
from app.inventory.api.router import router as inventory_router
from app.production.api.router import router as production_router
from app.planning.api.router import router as planning_router
from app.scheduling.api.router import router as scheduling_router
from app.reports.api.router import router as reports_router

app = FastAPI(title="APS - Advanced Planning & Scheduling", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api")
app.include_router(bom_router, prefix="/api")
app.include_router(orders_router, prefix="/api")
app.include_router(inventory_router, prefix="/api")
app.include_router(production_router, prefix="/api")
app.include_router(planning_router, prefix="/api")
app.include_router(scheduling_router, prefix="/api")
app.include_router(reports_router, prefix="/api")


@app.on_event("startup")
def startup():
    create_tables()
    _seed_demo_data()


def _seed_demo_data():
    from app.database import SessionLocal
    from app.auth.infrastructure.models import UserModel
    from app.auth.application.service import get_password_hash
    db = SessionLocal()
    try:
        if db.query(UserModel).count() == 0:
            db.add(UserModel(
                username="admin", email="admin@aps.com",
                password_hash=get_password_hash("admin123"), role="admin"
            ))
            db.add(UserModel(
                username="planner", email="planner@aps.com",
                password_hash=get_password_hash("planner123"), role="planner"
            ))
            db.commit()
    finally:
        db.close()


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "APS Backend"}
