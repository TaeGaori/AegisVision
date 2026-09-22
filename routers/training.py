from fastapi import APIRouter
from schemas.training import TrainingHistoryResponse
from services.training_service import get_training_history

router = APIRouter()

@router.get("/model/training-history", response_model=TrainingHistoryResponse)
def training_history():
    return get_training_history()