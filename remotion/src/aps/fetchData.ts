import { ApsReportData, FulfillmentRow, ScheduleDetail } from "./types";
import { SAMPLE_DATA } from "./sample";

// Configure where the APS backend lives and which account to use.
// Override at render time, e.g.:
//   APS_API_BASE=http://localhost:9000/api APS_USER=admin APS_PASSWORD=admin123 npm run render
const API_BASE =
  (typeof process !== "undefined" && process.env?.APS_API_BASE) ||
  "http://localhost:9000/api";
const USERNAME =
  (typeof process !== "undefined" && process.env?.APS_USER) || "admin";
const PASSWORD =
  (typeof process !== "undefined" && process.env?.APS_PASSWORD) || "admin123";

async function login(): Promise<string> {
  const body = new URLSearchParams({ username: USERNAME, password: PASSWORD });
  const res = await fetch(`${API_BASE}/auth/token`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
  if (!res.ok) throw new Error(`login failed: ${res.status}`);
  const json = (await res.json()) as { access_token: string };
  return json.access_token;
}

async function authGet<T>(path: string, token: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`GET ${path} failed: ${res.status}`);
  return (await res.json()) as T;
}

/**
 * Pull a live report bundle from the APS backend. Falls back to bundled
 * sample data if anything goes wrong (backend down, network blocked, no
 * schedules yet) so the video always renders.
 */
export async function fetchApsData(): Promise<ApsReportData> {
  try {
    const token = await login();
    const dashboard = await authGet<ApsReportData["dashboard"]>(
      "/reports/dashboard",
      token
    );
    const fulfillment = await authGet<FulfillmentRow[]>(
      "/reports/order-fulfillment",
      token
    );

    // Prefer the active schedule; otherwise the most recent one.
    const active = fulfillment.find((f) => f.status === "active");
    const target = active ?? fulfillment[0];
    let schedule: ScheduleDetail | null = null;
    if (target) {
      schedule = await authGet<ScheduleDetail>(
        `/scheduling/schedules/${target.schedule_id}`,
        token
      );
    }

    return {
      generatedAt: new Date().toISOString(),
      dashboard,
      fulfillment,
      schedule,
    };
  } catch (err) {
    // eslint-disable-next-line no-console
    console.warn(
      `[aps] live fetch failed, using sample data: ${
        err instanceof Error ? err.message : String(err)
      }`
    );
    return { ...SAMPLE_DATA, generatedAt: new Date().toISOString() };
  }
}
