# /auth/login 관련 요청/응답 형태

from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: str            # username
    role: str
    exp: int
