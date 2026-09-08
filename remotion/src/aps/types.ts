// Shapes mirror the APS backend JSON responses.
// - dashboard  -> GET /api/reports/dashboard
// - fulfillment-> GET /api/reports/order-fulfillment
// - schedule   -> GET /api/scheduling/schedules/{id}

export interface DashboardKpis {
  total_orders: number;
  open_orders: number;
  overdue_orders: number;
  total_products: number;
  fg_products: number;
  pending_net_requirements: number;
  overloaded_capacity_periods: number;
  active_schedule: string | null;
  active_schedule_on_time_rate: number;
  total_production_lines: number;
}

export interface FulfillmentRow {
  schedule_id: number;
  schedule_name: string;
  algorithm: string;
  total_jobs: number;
  on_time_jobs: number;
  on_time_rate: number;
  total_cost: number;
  utilization_rate: number;
  makespan_days: number;
  status: string;
}

export interface ScheduleItem {
  id: number;
  order_no: string;
  product_name: string;
  product_code: string;
  line_id: number;
  line_name: string;
  sequence: number;
  planned_quantity: number;
  start_datetime: string;
  end_datetime: string;
  cost: number;
  is_on_time: boolean;
}

export interface ScheduleDetail {
  id: number;
  name: string;
  algorithm: string;
  status: string;
  on_time_rate: number;
  total_cost: number;
  utilization_rate: number;
  makespan_days: number;
  items: ScheduleItem[];
}

// The full bundle a single video render consumes.
export interface ApsReportData {
  generatedAt: string;
  dashboard: DashboardKpis;
  fulfillment: FulfillmentRow[];
  schedule: ScheduleDetail | null;
}
