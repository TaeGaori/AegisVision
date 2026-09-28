# API Key 인증 의존성
# - 요청 헤더 X-API-Key 값을 .env에 등록된 키 목록과 대조
# - 라우터에서는 Depends(verify_api_key)만 붙이면 인증이 걸림

import os
from datetime import datetime, timedelta, timezone

from fastapi import Request, Security, HTTPException, status, Depends
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from jose import JWTError, jwt

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


# ── JWT 인증 (사람이 로그인해서 쓰는 대시보드/관리 기능용) ───────────────────
# API Key는 위에서 이미 처리했으므로, 여기서는 "로그인한 사용자" 흐름만 담당한다.

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-only-change-me")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

# tokenUrl은 Swagger UI(/docs)에서 "Authorize" 버튼이 로그인 요청을 보낼 주소
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def create_access_token(username: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload = {"sub": username, "role": role, "exp": expire}
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def get_current_user(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
) -> dict:
    """로그인 여부만 확인 (권한 무관). Depends(get_current_user)로 사용."""
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증 토큰이 유효하지 않습니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if token is None:
        raise credentials_error

    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except JWTError:
        raise credentials_error

    username = payload.get("sub")
    role = payload.get("role")
    if username is None or role is None:
        raise credentials_error

    # 감사 로그에서 API Key 클라이언트와 동일한 방식으로 조회되도록 재사용
    request.state.client_name = f"user:{username}"
    return {"username": username, "role": role}


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """관리자 전용 엔드포인트에 Depends(require_admin)으로 사용."""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다.",
        )
    return current_user
