from sqlalchemy.orm import Session
from sqlalchemy import func
from models.detection import Detection

def get_class_distribution(db: Session) -> dict:
    rows = (
        db.query(Detection.class_name, func.count(Detection.id))
        .group_by(Detection.class_name)
        .all()
    )
    return {class_name: count for class_name, count in rows}
