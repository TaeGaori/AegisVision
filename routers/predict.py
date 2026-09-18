# POST /predict, POST /predict/visualize 엔드포인트

from fastapi import APIRouter, UploadFile, File, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from PIL import Image
import io

from database import get_db
from schemas.prediction import PredictResponse
from services.inference import parse_detections, process_upload
from services.detection_service import save_detection_result

router = APIRouter()

@router.post('/predict', response_model=PredictResponse)
async def predict(file: UploadFile = File(...), db:Session = Depends(get_db)):
    result, inference_time_ms = await process_upload(file)

    detections = parse_detections(result)
    save_detection_result(db, file.filename, 'predict', inference_time_ms, detections)

    return PredictResponse(filename=file.filename, detections=detections)

@router.post('/predict/visualize')
async def predict_visualize(file: UploadFile = File(...), db:Session=Depends(get_db)):
    result, inference_time_ms = await process_upload(file)

    detections = parse_detections(result)
    save_detection_result(db, file.filename, 'predict_visualize', inference_time_ms, detections)

    plotted = result.plot()
    plotted_rgb = Image.fromarray(plotted[..., ::-1])

    buf = io.BytesIO()
    plotted_rgb.save(buf, format="JPEG")
    buf.seek(0)

    return StreamingResponse(buf, media_type='image/jpeg')