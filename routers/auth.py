# POST /auth/login - 사람이 로그인해서 JWT를 발급받는 엔드포인트

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from database import get_db
from core.security import create_access_token
from core.limiter import limiter
from schemas.auth import Token
from services.user_service import authenticate_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
@limiter.limit("5/minute")  # 로그인은 무차별 대입(brute force) 공격 대상이 되기 쉬워 더 엄격하게 제한
def login(
    request: Request,  # slowapi가 IP 확인을 위해 요구함
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="아이디 또는 비밀번호가 올바르지 않습니다.",
        )

    access_token = create_access_token(username=user.username, role=user.role)
    return Token(access_token=access_token)
