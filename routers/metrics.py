from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from models.detection import DetectionRequest, Detection
from schemas.model import MetricsResponse

router = APIRouter()

@router.get("/metrics", response_model=MetricsResponse)
def get_metrics(db: Session = Depends(get_db)):
    total_requests = db.query(DetectionRequest).count()

    total_detections = db.query(func.coalesce(func.sum(DetectionRequest.detection_count), 0)).scalar()

    avg_confidence = db.query(func.coalesce(func.avg(Detection.confidence), 0)).scalar()

    avg_inference_time_ms = db.query(func.coalesce(func.avg(DetectionRequest.inference_time_ms),0)).scalar()

    endpoint_counts = (db.query(DetectionRequest.endpoint, func.count(DetectionRequest.id)).group_by(DetectionRequest.endpoint).all())

    return MetricsResponse(
        total_requests = total_requests,
        total_detections = total_detections,
        avg_confidence = round(float(avg_confidence),3),
        avg_inference_time_ms = round(float(avg_inference_time_ms),1),
        requests_by_endpoint = {endpoint: count for endpoint, count in endpoint_counts}
    )