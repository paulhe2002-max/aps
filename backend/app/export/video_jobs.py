"""Background job manager for video report rendering.

Rendering a video can take from tens of seconds to a few minutes, which is too
long for a single blocking HTTP request. This module runs renders on a
background thread pool (one at a time — rendering is CPU heavy) and exposes a
simple in-memory job registry the API can poll.

Notes / limitations:
- The registry is in-process, so it fits a single uvicorn worker (as started by
  start.sh). For multi-worker / multi-instance deployments, back it with a
  shared store (Redis, DB) instead.
- Rendered files are written under a temp dir and cleaned up by TTL.
"""

from __future__ import annotations

import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import gettempdir
from typing import Literal, Optional

from .video_report import render_video, VideoRenderError

JobStatus = Literal["pending", "running", "done", "error"]

_JOBS_DIR = Path(gettempdir()) / "aps_video_jobs"
_JOBS_DIR.mkdir(parents=True, exist_ok=True)

# Keep finished jobs (and their files) for this long before cleanup.
_JOB_TTL_SECONDS = 60 * 60


@dataclass
class VideoJob:
    id: str
    status: JobStatus = "pending"
    created_at: float = field(default_factory=time.time)
    finished_at: Optional[float] = None
    error: Optional[str] = None
    file_path: Optional[str] = None
    filename: str = "APS_Report.mp4"

    def to_public(self) -> dict:
        return {
            "job_id": self.id,
            "status": self.status,
            "error": self.error,
            "created_at": self.created_at,
            "finished_at": self.finished_at,
            "ready": self.status == "done",
        }


_jobs: dict[str, VideoJob] = {}
_lock = threading.Lock()
# One render at a time — rendering saturates CPU.
_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="video-render")


def _cleanup_expired() -> None:
    now = time.time()
    with _lock:
        expired = [
            jid
            for jid, job in _jobs.items()
            if job.finished_at and now - job.finished_at > _JOB_TTL_SECONDS
        ]
        for jid in expired:
            job = _jobs.pop(jid)
            if job.file_path:
                Path(job.file_path).unlink(missing_ok=True)


def _run(job_id: str, data: dict) -> None:
    with _lock:
        job = _jobs.get(job_id)
        if not job:
            return
        job.status = "running"
    try:
        video_bytes = render_video(data)
        out_path = _JOBS_DIR / f"{job_id}.mp4"
        out_path.write_bytes(video_bytes)
        with _lock:
            job = _jobs.get(job_id)
            if job:
                job.status = "done"
                job.file_path = str(out_path)
                job.finished_at = time.time()
    except VideoRenderError as exc:
        _fail(job_id, str(exc))
    except Exception as exc:  # noqa: BLE001 - surface unexpected errors too
        _fail(job_id, f"渲染发生未预期错误：{exc}")


def _fail(job_id: str, detail: str) -> None:
    with _lock:
        job = _jobs.get(job_id)
        if job:
            job.status = "error"
            job.error = detail
            job.finished_at = time.time()


def create_job(data: dict, filename: str) -> VideoJob:
    """Register a job and schedule the render on the background pool."""
    _cleanup_expired()
    job = VideoJob(id=uuid.uuid4().hex, filename=filename)
    with _lock:
        _jobs[job.id] = job
    _executor.submit(_run, job.id, data)
    return job


def get_job(job_id: str) -> Optional[VideoJob]:
    with _lock:
        return _jobs.get(job_id)
