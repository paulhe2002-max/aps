#!/usr/bin/env node
// Fetch a live report bundle from the APS backend and write it to
// out/aps-data.json, so the video can be rendered offline with:
//   npm run render:file
//
// Env overrides:
//   APS_API_BASE (default http://localhost:9000/api)
//   APS_USER     (default admin)
//   APS_PASSWORD (default admin123)
import { writeFile, mkdir } from "node:fs/promises";

const API_BASE = process.env.APS_API_BASE || "http://localhost:9000/api";
const USERNAME = process.env.APS_USER || "admin";
const PASSWORD = process.env.APS_PASSWORD || "admin123";

async function login() {
  const body = new URLSearchParams({ username: USERNAME, password: PASSWORD });
  const res = await fetch(`${API_BASE}/auth/token`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
  if (!res.ok) throw new Error(`login failed: ${res.status}`);
  return (await res.json()).access_token;
}

async function get(path, token) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`GET ${path} failed: ${res.status}`);
  return res.json();
}

async function main() {
  const token = await login();
  const dashboard = await get("/reports/dashboard", token);
  const fulfillment = await get("/reports/order-fulfillment", token);
  const active = fulfillment.find((f) => f.status === "active") ?? fulfillment[0];
  let schedule = null;
  if (active) {
    schedule = await get(`/scheduling/schedules/${active.schedule_id}`, token);
  }
  const data = {
    generatedAt: new Date().toISOString(),
    dashboard,
    fulfillment,
    schedule,
  };
  await mkdir("out", { recursive: true });
  // Wrap in { data } so it can be passed directly as Remotion input props.
  await writeFile("out/aps-data.json", JSON.stringify({ data }, null, 2));
  console.log(
    `Wrote out/aps-data.json (${fulfillment.length} schedules, ${
      schedule?.items?.length ?? 0
    } jobs)`
  );
}

main().catch((err) => {
  console.error(err.message);
  process.exit(1);
});
