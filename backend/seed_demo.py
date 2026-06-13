"""Demo data seeding script for APS system."""
import sys
sys.path.insert(0, '/home/user/aps/backend')

from datetime import date, timedelta
from app.database import SessionLocal, create_tables
from app.auth.infrastructure.models import UserModel
from app.auth.application.service import get_password_hash
from app.bom.infrastructure.models import ProductModel, BomItemModel
from app.orders.infrastructure.models import CustomerOrderModel
from app.inventory.infrastructure.models import InventoryModel
from app.production.infrastructure.models import (
    ProductionLineModel, LineProductModel, WorkingCalendarModel, ChangeoverTimeModel
)


def seed():
    create_tables()
    db = SessionLocal()
    try:
        # Users
        if db.query(UserModel).count() == 0:
            db.add_all([
                UserModel(username="admin", email="admin@aps.com", password_hash=get_password_hash("admin123"), role="admin"),
                UserModel(username="planner", email="planner@aps.com", password_hash=get_password_hash("planner123"), role="planner"),
            ])
            db.commit()
            print("Users created")

        # Products
        if db.query(ProductModel).count() == 0:
            products = [
                ProductModel(code="FG-001", name="成品A - 电动工具", product_type="FG", unit="台", lead_time_days=3, safety_stock=50),
                ProductModel(code="FG-002", name="成品B - 手动工具套装", product_type="FG", unit="套", lead_time_days=2, safety_stock=30),
                ProductModel(code="FG-003", name="成品C - 精密仪器", product_type="FG", unit="台", lead_time_days=5, safety_stock=20),
                ProductModel(code="SFG-001", name="半成品A1 - 电机总成", product_type="SFG", unit="个", lead_time_days=2, safety_stock=100),
                ProductModel(code="SFG-002", name="半成品A2 - 外壳总成", product_type="SFG", unit="个", lead_time_days=1, safety_stock=80),
                ProductModel(code="SFG-003", name="半成品B1 - 工具手柄", product_type="SFG", unit="套", lead_time_days=1, safety_stock=60),
                ProductModel(code="RM-001", name="原材料 - 钢材", product_type="RM", unit="kg", lead_time_days=7, safety_stock=500),
                ProductModel(code="RM-002", name="原材料 - 塑料颗粒", product_type="RM", unit="kg", lead_time_days=5, safety_stock=300),
            ]
            db.add_all(products)
            db.commit()
            db.refresh(products[0])
            p_ids = {p.code: p.id for p in db.query(ProductModel).all()}

            # BOM
            bom_items = [
                BomItemModel(parent_product_id=p_ids["FG-001"], child_product_id=p_ids["SFG-001"], quantity=1, scrap_rate=0.02),
                BomItemModel(parent_product_id=p_ids["FG-001"], child_product_id=p_ids["SFG-002"], quantity=1, scrap_rate=0.01),
                BomItemModel(parent_product_id=p_ids["FG-002"], child_product_id=p_ids["SFG-003"], quantity=2, scrap_rate=0.01),
                BomItemModel(parent_product_id=p_ids["SFG-001"], child_product_id=p_ids["RM-001"], quantity=2.5, scrap_rate=0.05),
                BomItemModel(parent_product_id=p_ids["SFG-002"], child_product_id=p_ids["RM-002"], quantity=1.2, scrap_rate=0.03),
            ]
            db.add_all(bom_items)
            db.commit()
            print("Products & BOM created")

        # Orders
        if db.query(CustomerOrderModel).count() == 0:
            p_ids = {p.code: p.id for p in db.query(ProductModel).all()}
            today = date.today()
            orders = [
                CustomerOrderModel(order_no="SO-2024-001", product_id=p_ids["FG-001"], quantity=200, due_date=today + timedelta(days=15), priority=3, customer_name="华为技术"),
                CustomerOrderModel(order_no="SO-2024-002", product_id=p_ids["FG-002"], quantity=500, due_date=today + timedelta(days=10), priority=2, customer_name="小米集团"),
                CustomerOrderModel(order_no="SO-2024-003", product_id=p_ids["FG-003"], quantity=50, due_date=today + timedelta(days=20), priority=5, customer_name="比亚迪"),
                CustomerOrderModel(order_no="SO-2024-004", product_id=p_ids["FG-001"], quantity=300, due_date=today + timedelta(days=25), priority=4, customer_name="CATL"),
                CustomerOrderModel(order_no="SO-2024-005", product_id=p_ids["FG-002"], quantity=150, due_date=today + timedelta(days=8), priority=1, customer_name="宁德时代"),
                CustomerOrderModel(order_no="SO-2024-006", product_id=p_ids["FG-003"], quantity=80, due_date=today + timedelta(days=30), priority=6, customer_name="吉利汽车"),
            ]
            db.add_all(orders)
            db.commit()
            print("Orders created")

        # Inventory
        if db.query(InventoryModel).count() == 0:
            p_ids = {p.code: p.id for p in db.query(ProductModel).all()}
            inventories = [
                InventoryModel(product_id=p_ids["FG-001"], actual_stock=30, in_transit=20, wip=50),
                InventoryModel(product_id=p_ids["FG-002"], actual_stock=100, in_transit=0, wip=30),
                InventoryModel(product_id=p_ids["FG-003"], actual_stock=5, in_transit=10, wip=0),
                InventoryModel(product_id=p_ids["SFG-001"], actual_stock=80, in_transit=0, wip=60),
                InventoryModel(product_id=p_ids["SFG-002"], actual_stock=60, in_transit=20, wip=40),
                InventoryModel(product_id=p_ids["SFG-003"], actual_stock=120, in_transit=0, wip=0),
                InventoryModel(product_id=p_ids["RM-001"], actual_stock=800, in_transit=200, wip=0),
                InventoryModel(product_id=p_ids["RM-002"], actual_stock=400, in_transit=100, wip=0),
            ]
            db.add_all(inventories)
            db.commit()
            print("Inventory created")

        # Production Lines
        if db.query(ProductionLineModel).count() == 0:
            p_ids = {p.code: p.id for p in db.query(ProductModel).all()}
            lines = [
                ProductionLineModel(code="LINE-A", name="A线 - 电动工具线", capacity_per_shift=8, shifts_per_day=2, workers_per_shift=15),
                ProductionLineModel(code="LINE-B", name="B线 - 手动工具线", capacity_per_shift=8, shifts_per_day=2, workers_per_shift=10),
                ProductionLineModel(code="LINE-C", name="C线 - 精密仪器线", capacity_per_shift=8, shifts_per_day=1, workers_per_shift=8),
            ]
            db.add_all(lines)
            db.commit()

            line_ids = {l.code: l.id for l in db.query(ProductionLineModel).all()}

            # Line-Product mapping
            lps = [
                LineProductModel(line_id=line_ids["LINE-A"], product_id=p_ids["FG-001"], cycle_time_minutes=2.5, setup_time_minutes=30, cost_per_unit=15.0),
                LineProductModel(line_id=line_ids["LINE-B"], product_id=p_ids["FG-002"], cycle_time_minutes=1.5, setup_time_minutes=20, cost_per_unit=8.0),
                LineProductModel(line_id=line_ids["LINE-C"], product_id=p_ids["FG-003"], cycle_time_minutes=8.0, setup_time_minutes=60, cost_per_unit=45.0),
                LineProductModel(line_id=line_ids["LINE-A"], product_id=p_ids["SFG-001"], cycle_time_minutes=1.8, setup_time_minutes=20, cost_per_unit=10.0),
            ]
            db.add_all(lps)

            # Working Calendar - next 60 days
            today = date.today()
            for line_code, line_id in line_ids.items():
                shifts = 2 if line_code != "LINE-C" else 1
                for i in range(60):
                    d = today + timedelta(days=i)
                    is_weekend = d.weekday() >= 5
                    db.add(WorkingCalendarModel(
                        line_id=line_id,
                        work_date=d,
                        shift_count=0 if is_weekend else shifts,
                        available_hours=0 if is_weekend else shifts * 8.0,
                        is_holiday=is_weekend,
                    ))

            # Changeover times
            cos = [
                ChangeoverTimeModel(line_id=line_ids["LINE-A"], from_product_id=p_ids["FG-001"], to_product_id=p_ids["SFG-001"], changeover_minutes=45),
                ChangeoverTimeModel(line_id=line_ids["LINE-A"], from_product_id=p_ids["SFG-001"], to_product_id=p_ids["FG-001"], changeover_minutes=30),
            ]
            db.add_all(cos)
            db.commit()
            print("Production data created")

        print("Demo data seeding complete!")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
