from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
from ultralytics import YOLO
from PIL import Image
import io

app = FastAPI(
    title="AegisVision",
    description="드론/CCTV 영상 기반 객체 탐지")

model = YOLO('runs/detect/train/weights/last.pt')


@app.get('/')
def root():
    return{'message' : "AegisVision Drone Detection API"}


# 서버/모델 상태 확인 
@app.get('/health')
def health():
    return{
        'status' : "OK",
        'model_loaded' : model is not None,
    }


# 모델 정보 확인
@app.get('/model/info')
def model_info():
    return {
        "model_path" : "runs/detect/train/weights/last.pt",
        "classes" : model.names,
        "num_classes" : len(model.names)
    }


# 이미지 객체 탐지
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


# Bounding Box가 그려진 결과 이미지
@app.post('/predict/visualize')
async def predict_visualize(file: UploadFile = File(...)):
    image_bytes = await file.read()
    image = Image.open(io.BytesIO(image_bytes))

    results = model.predict(image, conf=0.25)

    # 박스가 그려진 이미지를 numpy array로 받아서 PIL로 변환
    plotted = results[0].plot()  # BGR 형식의 numpy array
    plotted_rgb = Image.fromarray(plotted[..., ::-1])  # BGR -> RGB 변환

    # 이미지를 바이트로 변환해서 응답
    buf = io.BytesIO()
    plotted_rgb.save(buf, format="JPEG")
    buf.seek(0)

    return StreamingResponse(buf, media_type="image/jpeg")


# metrics 추후 추가