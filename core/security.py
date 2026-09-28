# API Key 인증 의존성
# - 요청 헤더 X-API-Key 값을 .env에 등록된 키 목록과 대조
# - 라우터에서는 Depends(verify_api_key)만 붙이면 인증이 걸림

import os

from fastapi import Request, Security, HTTPException, status
from fastapi.security import APIKeyHeader

# .env 예시: API_KEYS=key-for-control-center,key-for-sensor-gateway-01
# 콤마로 여러 클라이언트의 키를 등록 (클라이언트별로 다른 키를 발급해두면
# 감사 로그에서 "누가 호출했는지"를 API 키 이름으로 구분할 수 있음)
_raw_keys = os.getenv("API_KEYS", "")
VALID_API_KEYS: dict[str, str] = {}
for pair in _raw_keys.split(","):
    pair = pair.strip()
    if not pair:
        continue
    # key=클라이언트이름 형식이면 이름까지 기록, 아니면 키 자체를 이름으로 사용
    if "=" in pair:
        key_value, client_name = pair.split("=", 1)
    else:
        key_value, client_name = pair, pair[:8] + "..."
    VALID_API_KEYS[key_value] = client_name

# auto_error=False로 두고 우리가 직접 401을 던져서 에러 메시지를 통일
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(
    request: Request,
    api_key: str | None = Security(api_key_header),
) -> str:
    """
    라우터에 Depends(verify_api_key)로 붙이는 인증 의존성.
    반환값(client_name)은 request.state에도 담아 감사 로그(middleware)에서 재사용한다.
    """
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-API-Key 헤더가 필요합니다.",
        )

    client_name = VALID_API_KEYS.get(api_key)
    if client_name is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 API Key입니다.",
        )

    request.state.client_name = client_name
    return client_name
