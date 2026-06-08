from fastapi import APIRouter

from app.schemas.common import MessageResponse

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/health", response_model=MessageResponse)
def health():
    return {"message": "ok"}
