# /health, /model/info 응답 형태 (HealthResponse, ModelInfoResponse)

from pydantic import BaseModel

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool

class ModelInfoResponse(BaseModel):
    model_path: str
    classes: dict[int, str]
    num_classes: int
