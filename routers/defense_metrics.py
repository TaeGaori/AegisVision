import json
from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from services.metrics_service import get_class_distribution

router = APIRouter()

DEFENSE_METRICS_FILE = Path("defense_metrics.json")

@router.get("/metrics/defense")
def defense_metrics(db:Session = Depends(get_db)):
    offline_metrics = {}
    if DEFENSE_METRICS_FILE.exists():
        with open(DEFENSE_METRICS_FILE) as f:
            offline_metrics = json.load(f)

    return {
    "low_fpr_recall": offline_metrics.get("low_fpr_recall"),
    "fps_benchmark": offline_metrics.get("fps_benchmark"),
    "class_distribution": get_class_distribution(db),
    }