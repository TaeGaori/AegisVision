# 업로드 파일 검증 - 크기 제한 + 실제 이미지인지 확인
# 확장자(.jpg 등)만 보는 방식은 파일명만 바꾸면 우회되므로,
# PIL로 실제로 열어서 진짜 이미지인지 검증한다 (매직 바이트 검증과 동일한 효과)

import io

from fastapi import UploadFile, HTTPException, status
from PIL import Image, UnidentifiedImageError

MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024  # 10MB
ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "BMP", "WEBP"}



async def validate_and_read_upload(file: UploadFile) -> bytes:
    image_bytes = await file.read(MAX_UPLOAD_SIZE_BYTES + 1)

    # 1) 크기 제한
    if len(image_bytes) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"파일 크기는 {MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)}MB를 초과할 수 없습니다.",
        )

    if len(image_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="빈 파일입니다.",
        )

    # 2) 실제 이미지인지 검증 (확장자가 아니라 파일 내용 기준)
    try:
        image = Image.open(io.BytesIO(image_bytes))
        image.verify()  # 손상된 이미지인지 확인
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError, Image.DecompressionBombError):
        raise HTTPException(status_code=400, detail="이미지 파일이 아니거나 손상되었습니다.")

    # verify() 이후에는 파일 핸들이 소모되므로, 포맷 확인은 새로 한번 더 연다
    image_format = Image.open(io.BytesIO(image_bytes)).format
    if image_format not in ALLOWED_IMAGE_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"지원하지 않는 이미지 형식입니다: {image_format} (허용: {', '.join(ALLOWED_IMAGE_FORMATS)})",
        )

    return image_bytes
