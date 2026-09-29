# 감사 로그(Audit Log) 테이블 - 누가/언제/어디서/무엇을 호출했는지 기록

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    client_ip: Mapped[str] = mapped_column(String(64), nullable=False)
    # verify_api_key()가 반환한 클라이언트 식별 이름 (인증 실패 시 None)
    client_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    method: Mapped[str] = mapped_column(String(10), nullable=False)
    path: Mapped[str] = mapped_column(String(255), nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    process_time_ms: Mapped[float] = mapped_column(Float, nullable=False)
