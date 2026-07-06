from fastapi import APIRouter
from fastapi.responses import Response
from .user_manual import generate_user_manual
from .algo_demo import generate_algorithm_demo

router = APIRouter(prefix="/export", tags=["export"])


@router.get("/user-manual", summary="下载用户操作手册 Excel")
def download_user_manual():
    data = generate_user_manual()
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=APS_用户操作手册.xlsx"},
    )


@router.get("/algorithm-demo", summary="下载算法逐步演示 Excel")
def download_algorithm_demo():
    data = generate_algorithm_demo()
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=APS_算法逐步演示.xlsx"},
    )
