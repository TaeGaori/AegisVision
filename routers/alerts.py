from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database import get_db
from models.detection import Detection, DetectionRequest

router = APIRouter()

@router.get("/alerts")
def get_alerts(db:Session = Depends(get_db), limit: int = 20):
    high_threat = (
        db.query(Detection, DetectionRequest)
        .join(DetectionRequest, Detection.request_id == DetectionRequest.id)
        .filter(Detection.threat_level.in_(["high", "critical"]))
        .order_by(desc(DetectionRequest.requested_at))
        .limit(limit)
        .all()
    )

    return[
        {
            "filename": req.filename,
            "class_name": det.class_name,
            "confidence": det.confidence,
            "threat_level": det.threat_level,
            "detected_at": str(req.requested_at),
        }
        for det, req in high_threat
    ]