# YOLO 모델을 한 번만 로드해서 재사용 (싱글턴 관리)
from ultralytics import YOLO

MODEL_PATH = 'runs/detect/train/weights/last.pt'

class ModelManager:
    # 모델 로드/조회를 한 곳에서 관리
    _instance: YOLO | None = None

    @classmethod
    def get_model(cls) -> YOLO:
        if cls._instance is None:
            cls._instance = YOLO(MODEL_PATH)
        return cls._instance

    @classmethod
    def get_model_path(cls) -> str:
        return MODEL_PATH

    
model_manager = ModelManager()