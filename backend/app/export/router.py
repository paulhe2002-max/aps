from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import quote
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth.api.router import get_current_active_user
from .user_manual import generate_user_manual
from .algo_demo import generate_algorithm_demo
from .video_report import generate_video_report, build_report_data, VideoRenderError
from . import video_jobs

router = APIRouter(prefix="/export", tags=["export"])


def _attachment(filename: str) -> str:
    ascii_name = filename.encode("ascii", errors="ignore").decode()
    encoded = quote(filename, encoding="utf-8")
    return f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{encoded}"


@router.get("/user-manual", summary="下载用户操作手册 Excel")
def download_user_manual():
    data = generate_user_manual()
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": _attachment("APS_User_Manual.xlsx")},
    )


@router.get("/algorithm-demo", summary="下载算法逐步演示 Excel")
def download_algorithm_demo():
    data = generate_algorithm_demo()
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": _attachment("APS_Algorithm_Demo.xlsx")},
    )


@router.get("/video-report", summary="一键生成 APS 视频报告 (MP4)")
def download_video_report(
    schedule_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_active_user),
):
    """读取最新的 APS 数据（看板 / 排产方案 / 甘特图）并渲染成 MP4 视频报告。

    可选 ``schedule_id`` 指定要展示的排产方案，缺省使用活跃方案。
    渲染由 remotion/ 工程完成，需服务器已安装 Node.js 且执行过 `npm install`。
    """
    try:
        video_bytes = generate_video_report(db, schedule_id)
    except VideoRenderError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    return Response(
        content=video_bytes,
        media_type="video/mp4",
        headers={"Content-Disposition": _attachment(f"APS_Report_{stamp}.mp4")},
    )


# ---------------------------------------------------------------------------
# Async (non-blocking) video generation: start a job, poll status, download.
# Preferred over the synchronous endpoint above since rendering is slow.
# ---------------------------------------------------------------------------


@router.post("/video-report/jobs", summary="启动视频报告渲染任务（异步）")
def start_video_report_job(
    schedule_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_active_user),
):
    """组装最新数据并在后台开始渲染，立即返回 job_id 供轮询。"""
    # Build the data bundle now (fast DB queries) while we hold the session,
    # then hand it to the background renderer.
    data = build_report_data(db, schedule_id)
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    job = video_jobs.create_job(data, filename=f"APS_Report_{stamp}.mp4")
    return job.to_public()


@router.get("/video-report/jobs/{job_id}", summary="查询视频报告任务状态")
def get_video_report_job(
    job_id: str,
    user=Depends(get_current_active_user),
):
    job = video_jobs.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="任务不存在或已过期")
    return job.to_public()


@router.get("/video-report/jobs/{job_id}/download", summary="下载已渲染的视频报告")
def download_video_report_job(
    job_id: str,
    user=Depends(get_current_active_user),
):
    job = video_jobs.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="任务不存在或已过期")
    if job.status == "error":
        raise HTTPException(status_code=503, detail=job.error or "渲染失败")
    if job.status != "done" or not job.file_path or not Path(job.file_path).exists():
        raise HTTPException(status_code=409, detail="视频尚未渲染完成")
    return FileResponse(
        path=job.file_path,
        media_type="video/mp4",
        headers={"Content-Disposition": _attachment(job.filename)},
    )
