from fastapi import APIRouter

router = APIRouter()


@router.get("/healthz", summary="存活探针")
def healthz():
    return {"ok": True}
