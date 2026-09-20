# 탐지 결과를 models의 테이블 구조로 변환해 DB에 저장

from sqlalchemy.orm import Session
from models.detection import DetectionRequest, Detection
from services.model_manager import model_manager


def save_detection_result(
        db: Session,
        filename: str,
        endpoint: str,
        inference_time_ms: float,
        detections: list[dict]
)   -> DetectionRequest:

    try:
        db_request = DetectionRequest(
            filename=filename,
            endpoint=endpoint,
            model_path=model_manager.get_model_path(),
            inference_time_ms=inference_time_ms,
            detection_count=len(detections)
        )
        db.add(db_request)

        # SQL을 보내서 id를 받아오되 트랜잭션은 아직 안 끝남
        db.flush()

        for d in detections:
            db.add(Detection(
                request_id=db_request.id,
                class_name=d["class_name"],
                confidence=d["confidence"],
                bbox_x1=d["bbox"][0],
                bbox_y1=d["bbox"][1],
                bbox_x2=d["bbox"][2],
                bbox_y2=d["bbox"][3]
            ))
        db.commit()
        db.refresh(db_request)

        return db_request

    except Exception:
        db.rollback()
        raise