import { ApsReportData } from "./types";

// Offline fallback used when the APS backend is unreachable (CI/sandbox, or
// before the stack is running). Values mirror backend/seed_demo.py so the
// video looks realistic without a live database.
export const SAMPLE_DATA: ApsReportData = {
  generatedAt: new Date().toISOString(),
  dashboard: {
    total_orders: 6,
    open_orders: 6,
    overdue_orders: 1,
    total_products: 8,
    fg_products: 3,
    pending_net_requirements: 5,
    overloaded_capacity_periods: 2,
    active_schedule: "EDD 排产方案",
    active_schedule_on_time_rate: 83.3,
    total_production_lines: 3,
  },
  fulfillment: [
    {
      schedule_id: 3,
      schedule_name: "EDD 排产方案",
      algorithm: "EDD",
      total_jobs: 6,
      on_time_jobs: 5,
      on_time_rate: 83.3,
      total_cost: 128500,
      utilization_rate: 78.4,
      makespan_days: 12.5,
      status: "active",
    },
    {
      schedule_id: 2,
      schedule_name: "SPT 排产方案",
      algorithm: "SPT",
      total_jobs: 6,
      on_time_jobs: 4,
      on_time_rate: 66.7,
      total_cost: 121000,
      utilization_rate: 81.2,
      makespan_days: 11.8,
      status: "draft",
    },
  ],
  schedule: {
    id: 3,
    name: "EDD 排产方案",
    algorithm: "EDD",
    status: "active",
    on_time_rate: 83.3,
    total_cost: 128500,
    utilization_rate: 78.4,
    makespan_days: 12.5,
    items: [
      { id: 1, order_no: "SO-2024-005", product_name: "成品B - 手动工具套装", product_code: "FG-002", line_id: 2, line_name: "B线 - 手动工具线", sequence: 1, planned_quantity: 150, start_datetime: "2024-01-08T06:00:00", end_datetime: "2024-01-09T14:00:00", cost: 12000, is_on_time: true },
      { id: 2, order_no: "SO-2024-002", product_name: "成品B - 手动工具套装", product_code: "FG-002", line_id: 2, line_name: "B线 - 手动工具线", sequence: 2, planned_quantity: 500, start_datetime: "2024-01-09T14:00:00", end_datetime: "2024-01-12T18:00:00", cost: 40000, is_on_time: true },
      { id: 3, order_no: "SO-2024-001", product_name: "成品A - 电动工具", product_code: "FG-001", line_id: 1, line_name: "A线 - 电动工具线", sequence: 1, planned_quantity: 200, start_datetime: "2024-01-08T06:00:00", end_datetime: "2024-01-10T12:00:00", cost: 15000, is_on_time: true },
      { id: 4, order_no: "SO-2024-004", product_name: "成品A - 电动工具", product_code: "FG-001", line_id: 1, line_name: "A线 - 电动工具线", sequence: 2, planned_quantity: 300, start_datetime: "2024-01-10T12:00:00", end_datetime: "2024-01-14T16:00:00", cost: 22500, is_on_time: true },
      { id: 5, order_no: "SO-2024-003", product_name: "成品C - 精密仪器", product_code: "FG-003", line_id: 3, line_name: "C线 - 精密仪器线", sequence: 1, planned_quantity: 50, start_datetime: "2024-01-08T06:00:00", end_datetime: "2024-01-11T20:00:00", cost: 22500, is_on_time: true },
      { id: 6, order_no: "SO-2024-006", product_name: "成品C - 精密仪器", product_code: "FG-003", line_id: 3, line_name: "C线 - 精密仪器线", sequence: 2, planned_quantity: 80, start_datetime: "2024-01-11T20:00:00", end_datetime: "2024-01-17T10:00:00", cost: 16500, is_on_time: false },
    ],
  },
};
