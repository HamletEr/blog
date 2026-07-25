from fastapi import APIRouter

router: APIRouter = APIRouter(
    prefix="/health",
    tags=["health"],
)


@router.get("/live")
async def live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
async def ready() -> dict[str, str]:
    return {"status": "unknown"}  # TODO add a database connection check
