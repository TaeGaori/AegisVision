# GET /model/info 엔드포인트
from fastapi import APIRouter
from schemas.model import ModelInfoResponse
from services.model_manager import model_manager

router = APIRouter()

@router.get("/model/info", response_model=ModelInfoResponse)
def model_into():
    model = model_manager.get_model()
    return ModelInfoResponse(
        model_path=model_manager.get_model_path(),
        classes=model.names,
        num_classes=len(model.names)
    )