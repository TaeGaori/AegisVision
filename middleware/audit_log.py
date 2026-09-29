# 모든 요청을 감사 로그(audit_logs)에 기록하는 미들웨어
# - 인증(Depends)은 라우터 단에서, 로깅은 여기서 - 역할을 분리한다
# - Caddy/nginx 뒤에 배포하는 경우 X-Forwarded-For를 신뢰해야 실제 발신 IP가 남는다
#   (프록시 없이 직접 노출된 상태라면 request.client.host가 곧 실제 IP)

import time
import logging

from fastapi import FastAPI, Request
from fastapi.concurrency import run_in_threadpool

from database import Sessionmaker
from models.audit import AuditLog

logger = logging.getLogger("audit")
SKIP_PATHS = {"/health"}


def _write_audit_log(**fields) -> None:   # ★ 추가 (함수 전체)
    db = Sessionmaker()
    try:
        db.add(AuditLog(**fields))
        db.commit()
    except Exception:
        logger.exception("감사 로그 저장 실패")
        db.rollback()
    finally:
        db.close()


def _get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        # "클라이언트IP, 프록시1IP, 프록시2IP" 형태이므로 첫 번째 값이 실제 발신지
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def register_audit_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def audit_log_middleware(request: Request, call_next):
        start_time = time.time()

        response = await call_next(request)

        if request.url.path in SKIP_PATHS:
            return response

        process_time_ms = (time.time() - start_time) * 1000
        client_ip = _get_client_ip(request)
        # core.security.verify_api_key()가 인증에 성공하면 request.state.client_name에 심어둔 값
        client_name = getattr(request.state, "client_name", None)

        await run_in_threadpool(
            _write_audit_log,
            client_ip=client_ip,
            client_name=client_name,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            process_time_ms=process_time_ms,
        )

        return response
