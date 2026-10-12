# POST /predict, POST /predict/visualize 엔드포인트

from fastapi import APIRouter, UploadFile, File, Depends
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from PIL import Image
import io

from database import get_db
from schemas.prediction import PredictResponse
from services.inference import parse_detections, process_image_bytes
from services.detection_service import save_detection_result
from services.upload_validation import validate_and_read_upload



router = APIRouter()

def _infer_and_save(db:Session, image_bytes: bytes, filename: str, endpoint: str):
    """추론 + DB 저장을 한 덩어리로 묶어 스레드풀에서 실행하기 위한 동기 함수"""
    result, inference_time_ms = process_image_bytes(image_bytes)
    detections = parse_detections(result)
    save_detection_result(db, filename, endpoint, inference_time_ms, detections)
    return result, detections


@router.post('/predict', response_model=PredictResponse)
async def predict(file: UploadFile = File(...), db:Session = Depends(get_db)):
    image_bytes = await validate_and_read_upload(file)
    _, detections = await run_in_threadpool(
        _infer_and_save, db, image_bytes, file.filename, 'predict'
    )
    return PredictResponse(filename=file.filename, detections=detections)


@router.post('/predict/visualize', response_class=StreamingResponse,
            #  Swagger문서에서 이 엔드포인트가 이미지를 반환한다는 걸 명시적으로 보여줌
             responses={200:{"content":{"image/jpeg": {}}, "description":"객체 탐지 결과 이미지"}})
async def predict_visualize(file: UploadFile = File(...), db:Session=Depends(get_db)):
    image_bytes = await validate_and_read_upload(file)
    result, _ = await run_in_threadpool(
        _infer_and_save, db, image_bytes, file.filename, 'predict_visualize'
    )

    # 박스 그리기
    def _render() -> io.BytesIO:
        plotted = result.plot() # BGR numpy 배열
        img = Image.fromarray(plotted[..., ::-1])   # BGR -> RGB  [..., ::-1] -> 높이, 너비, 채널
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        buf.seek(0)
        return buf

    buf = await run_in_threadpool(_render)
    return StreamingResponse(buf, media_type='image/jpeg')