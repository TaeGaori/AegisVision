# /health, /model/info, /metrics 응답 형태 (HealthResponse, ModelInfoResponse, MetricsResponse)

from pydantic import BaseModel

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool

class ModelInfoResponse(BaseModel):
    model_path: str
    classes: dict[int, str]
    num_classes: int

class MetricsResponse(BaseModel):
    total_requests: int
    total_detections: int
    avg_confidence: float
    avg_inference_time_ms: float
    requests_by_endpoint: dict[str, int]
