# JWT 로그인용 사용자 테이블
# - API Key(core/security.py)는 "기계 대 기계"(센서 게이트웨이 등) 호출용
# - User/JWT는 "사람이 로그인해서 대시보드/관리 기능을 쓰는" 용도로 역할을 나눈다

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    # "admin": 학습 이력/재학습 등 민감한 기능 접근 가능, "viewer": 조회만 가능
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="viewer")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
