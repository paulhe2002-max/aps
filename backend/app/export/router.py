from datetime import datetime
from typing import Optional
from urllib.parse import quote
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth.api.router import get_current_active_user
from .user_manual import generate_user_manual
from .algo_demo import generate_algorithm_demo
from .video_report import generate_video_report, VideoRenderError

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
