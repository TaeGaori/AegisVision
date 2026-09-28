# 요청 빈도 제한(Rate Limiting) - slowapi
# 기본 키는 IP지만, Caddy 뒤에서는 X-Forwarded-For를 봐야 실제 발신 IP를 구분할 수 있다.

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request


def _rate_limit_key(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return get_remote_address(request)


limiter = Limiter(key_func=_rate_limit_key)
