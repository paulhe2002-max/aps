from urllib.parse import quote
from fastapi import APIRouter
from fastapi.responses import Response
from .user_manual import generate_user_manual
from .algo_demo import generate_algorithm_demo

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
