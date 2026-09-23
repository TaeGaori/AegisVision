# /model/training-history 응답 형태 (TrainingHistoryResponse)

from pydantic import BaseModel

class TrainingRun(BaseModel):
    run_name : str
    run_id : str
    status: str
    epochs: int # 목표
    actual_epochs: int  # 실제 완료 epoch
    mAP50: float | None = None
    mAP50_95: float | None = None
    precision: float | None = None
    recall: float | None = None
    started_at : str

class CumulativePoint(BaseModel):
    step: int
    value: float


class TrainingHistoryResponse(BaseModel):
    total_sessions: int
    total_epochs: int
    runs: list[TrainingRun]
    cumulative_metrics: dict[str, list[CumulativePoint]] = {}