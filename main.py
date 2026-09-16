from fastapi import FastAPI, UploadFile, File
from ultralytics import YOLO
from PIL import Image
import io

app = FastAPI(
    title="AegisVision",
    description="드론/CCTV 영상 기반 객체 탐지")

model = YOLO('runs/detect/train/weights/yolo26n.pt')

@app.get('/')
def root():
    return{'message' : "AegisVision Drone Detection API"}

@app.post('/predict')
async def predict(file: UploadFile = File(...)):
    # 업로드 이미지 PIL 이미지로 변환
    image_bytes = await file.read()
    image = Image.open(io.BytesIO(image_bytes))

    # YOLO 추론
    results = model.predict(image, conf=0.25)

    # 결과를 JSON으로 정리
    detections = []
    for box in results[0].boxes:
        detections.append({
            'class':model.names[int(box.cls)],
            'confidence': float(box.conf),
            'bbox': box.xyxy[0].tolist()
        })

    return{
        'filename': file.filename,
        'detections': detections
    }