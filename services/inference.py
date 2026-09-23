# YOLO 모델로 추론 실행 + 결과를 dict로 변환

from services.model_manager import model_manager
from PIL import Image
import time
import io


# 학습된 모델을 활용해 추론
def run_inference(image: Image.Image):
    model = model_manager.get_model()
    results = model.predict(image, conf=0.5)
    return results[0]

def parse_detections(result) -> list[dict]:
    detections = []
    for box in result.boxes:
        detections.append({
            "class_name": result.names[int(box.cls)],
            "confidence": float(box.conf),
            "bbox": box.xyxy[0].tolist()
        })
    return detections

async def process_upload(file) -> tuple:
    image_bytes = await file.read()
    image = Image.open(io.BytesIO(image_bytes))

    start_time =time.time()
    result = run_inference(image)
    inference_time_ms = (time.time() - start_time) * 1000

    return result, inference_time_ms