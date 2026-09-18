# /predict 관련 응답 형태 (DetectionResult, PredictResponse)

from pydantic import BaseModel

class DetectionResult(BaseModel):
    class_name: str
    confidence: float
    bbox: list[float]   #[x1, y1, x2, y2]

class PredictResponse(BaseModel):
    filename: str
    detections: list[DetectionResult]