from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from PIL import Image
import io, os, json
import tempfile

from fastapi.responses import FileResponse
from services.video_inference import process_video
from fastapi.concurrency import run_in_threadpool

router = APIRouter()

@router.post('/predict/video')
async def predict_video(file: UploadFile = File(...)):
    # 임시 파일로 저장 (비디오는 메미로째 올리기엔 큼)
    suffix = os.path.splitext(file.filename)[1]

    content = await file.read()

    MAX_VIDEO_SIZE_BYTES = 50 * 1024 * 1024   # 50MB
    if len(content) > MAX_VIDEO_SIZE_BYTES:
        raise HTTPException(413, "비디오는 50MB를 초과할 수 없습니다.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix)as tmp:
        tmp.write(content)
        input_path = tmp.name

    try:
        output_path, summary = await run_in_threadpool(process_video,input_path)
    except ValueError as e:
        os.remove(input_path)
        raise HTTPException(status_code=400, detail=str(e))

    os.remove(input_path)

    return FileResponse(
        output_path,
        media_type="video/mp4",
        filename='detected_video.mp4',
        headers={"X-Detection-Summary": json.dumps(summary)}
    )