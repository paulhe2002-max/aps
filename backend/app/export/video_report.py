"""One-click video report generation.

Assembles the same data bundle the frontend charts consume (dashboard KPIs,
schedule fulfillment comparison, and the active schedule's Gantt items),
then renders it into an MP4 with the Remotion project under ``remotion/``.

The Remotion render runs as a subprocess (Node.js + the remotion project's
dependencies must be installed). Data is passed to Remotion via a temporary
``--props`` file, and ``APS_SKIP_FETCH=1`` tells the composition to use that
data instead of calling back into the API.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.reports.api.router import dashboard_kpis, order_fulfillment
from app.scheduling.application.service import get_schedule, get_schedule_items


# Repo root is three levels up from this file: backend/app/export/ -> repo root.
_REPO_ROOT = Path(__file__).resolve().parents[3]
REMOTION_DIR = Path(os.environ.get("REMOTION_DIR", _REPO_ROOT / "remotion"))
COMPOSITION_ID = "ApsReport"
RENDER_TIMEOUT_SECONDS = int(os.environ.get("REMOTION_RENDER_TIMEOUT", "600"))


class VideoRenderError(RuntimeError):
    """Raised when the video cannot be generated, with a human-readable reason."""


def build_report_data(db: Session, schedule_id: int | None = None) -> dict:
    """Assemble the report bundle consumed by the Remotion composition."""
    dashboard = dashboard_kpis(db=db, user=None)
    fulfillment = order_fulfillment(db=db, user=None)

    # Pick the requested schedule, else the active one, else the most recent.
    target_id = schedule_id
    if target_id is None:
        active = next((f for f in fulfillment if f["status"] == "active"), None)
        target = active or (fulfillment[0] if fulfillment else None)
        target_id = target["schedule_id"] if target else None

    schedule = None
    if target_id is not None:
        s = get_schedule(db, target_id)
        if s:
            schedule = {
                "id": s.id,
                "name": s.name,
                "algorithm": s.algorithm,
                "status": s.status,
                "on_time_rate": s.on_time_rate,
                "total_cost": s.total_cost,
                "utilization_rate": s.utilization_rate,
                "makespan_days": s.makespan_days,
                "items": get_schedule_items(db, target_id),
            }

    return {
        "generatedAt": datetime.now().isoformat(),
        "dashboard": dashboard,
        "fulfillment": fulfillment,
        "schedule": schedule,
    }


def _resolve_node_runner() -> list[str]:
    """Return the base command used to invoke the Remotion CLI."""
    npx = shutil.which("npx")
    if npx:
        return [npx, "remotion"]
    raise VideoRenderError(
        "未找到 Node.js/npx，无法渲染视频。请在服务器上安装 Node.js 并在 "
        "remotion/ 目录执行 `npm install`。"
    )


def render_video(data: dict) -> bytes:
    """Render the report bundle into an MP4 and return its bytes."""
    if not REMOTION_DIR.exists():
        raise VideoRenderError(f"Remotion 工程目录不存在：{REMOTION_DIR}")
    if not (REMOTION_DIR / "node_modules").exists():
        raise VideoRenderError(
            f"Remotion 依赖未安装。请在 {REMOTION_DIR} 执行 `npm install`。"
        )

    base_cmd = _resolve_node_runner()

    with tempfile.TemporaryDirectory() as tmp:
        props_path = Path(tmp) / "props.json"
        out_path = Path(tmp) / "aps-report.mp4"
        props_path.write_text(json.dumps({"data": data}), encoding="utf-8")

        cmd = [
            *base_cmd,
            "render",
            COMPOSITION_ID,
            str(out_path),
            f"--props={props_path}",
            "--log=error",
        ]
        # Optional: point at a preinstalled Chrome Headless Shell to avoid the
        # runtime download (useful in restricted networks / containers).
        browser = os.environ.get("REMOTION_BROWSER_EXECUTABLE")
        if browser:
            cmd.append(f"--browser-executable={browser}")

        # Remotion only forwards REMOTION_-prefixed env vars into the bundle,
        # so the composition reads REMOTION_APS_SKIP_FETCH to use our props.
        env = {**os.environ, "REMOTION_APS_SKIP_FETCH": "1"}

        try:
            proc = subprocess.run(
                cmd,
                cwd=str(REMOTION_DIR),
                env=env,
                capture_output=True,
                text=True,
                timeout=RENDER_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            raise VideoRenderError(
                f"视频渲染超时（>{RENDER_TIMEOUT_SECONDS}s）。"
            )

        if proc.returncode != 0 or not out_path.exists():
            detail = (proc.stderr or proc.stdout or "").strip()[-800:]
            raise VideoRenderError(f"视频渲染失败：\n{detail}")

        return out_path.read_bytes()


def generate_video_report(db: Session, schedule_id: int | None = None) -> bytes:
    """Convenience: build data + render in one call."""
    data = build_report_data(db, schedule_id)
    return render_video(data)
