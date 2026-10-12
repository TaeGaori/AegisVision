import os
import json
import tempfile

from fastapi.responses import FileResponse
from services.video_inference import process_video
from fastapi.concurrency import run_in_threadpool
from fastapi import APIRouter, UploadFile, File, HTTPException
from starlette.background import BackgroundTask

router = APIRouter()

MAX_VIDEO_SIZE_BYTES = 50 * 1024 * 1024 # 50MB
CHUNK_SIZE = 1024 * 1024    # 1MB씩 읽기

def _safe_remove(path: str) -> None:
    """파일이 이미 없어도 에러를 내지 않는 삭제 (정리 코드는 절대 예외를 던지면 안 됨)"""
    try:
        os.remove(path)
    except FileNotFoundError:
        pass

async def _save_upload_with_limit(file: UploadFile, suffix: str) -> str:
    """업로드를 임시 파일로 저장하되 크기 한도를 넘으면 중단하고 파일을 지운다."""
    fd, path = tempfile.mkstemp(suffix=suffix)
    total = 0
    try:
        with os.fdopen(fd,"wb") as out:
            while True:
                chunk = await file.read(CHUNK_SIZE)
                if not chunk:
                    break
                # 한도가 넘는 청크는 413에러 반환
                total += len(chunk)
                if total > MAX_VIDEO_SIZE_BYTES:
                    raise HTTPException(413, "비디오는 50MB를 초과할 수 없습니다.")
                out.write(chunk)
    # 실패시 삭제하고 예외는 그대로 전달
    except BaseException:
        _safe_remove(path)
        raise
    return path

@router.post('/predict/video')
async def predict_video(file: UploadFile = File(...)):
    # 파일일의 확장자를 가져오고 없다면 .mp4를 반환
    suffix = os.path.splitext(file.filename or "")[1] or ".mp4"
    input_path = await _save_upload_with_limit(file,suffix)

    try:
        # 영상 처리(포장)
        output_path, summary = await run_in_threadpool(process_video, input_path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        # 성공/실패 모두에서 입력 파일 정리
        _safe_remove(input_path)

    return FileResponse(
        output_path,
        media_type="video/mp4",
        filename='detected_video.mp4',
        headers={"X-Detection-Summary": json.dumps(summary)},
        # 파일 전송 후 지우도록 예약
        background=BackgroundTask(_safe_remove, output_path),
    )
