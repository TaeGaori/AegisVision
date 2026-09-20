# GET /health 엔드포인트

from fastapi import APIRouter
from schemas.model import HealthResponse
from services.model_manager import model_manager

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
def health():
    model = model_manager.get_model()
    return HealthResponse(status="ok", model_loaded=model is not None)