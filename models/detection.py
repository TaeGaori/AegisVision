# DB에 들어갈 테이블 구조

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


# 이미지 객체 탐지 테이블
class DetectionRequest(Base):
    __tablename__ = "detection_requests"

    id: Mapped[int] = mapped_column(primary_key=True)   # 기본키
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    endpoint: Mapped[str] = mapped_column(String(50), nullable=False)
    requested_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    model_path: Mapped[str] = mapped_column(String(255), nullable=False)
    # 시간을 저장하는 거라 datetime 사용 -> 밀리초를 저장하는 거라 float 사용
    inference_time_ms: Mapped[float] = mapped_column(Float, nullable=True)
    detection_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    detections: Mapped[list['Detection']] = relationship(back_populates='request',
                                                cascade='all, delete-orphan'
                                                )

    
class Detection(Base):
    __tablename__ = "detections"

    id: Mapped[int] = mapped_column(primary_key=True)
    # ondelete='CASCADE' -> DB제약조건 이중으로 보호
    request_id: Mapped[int] = mapped_column(Integer, ForeignKey('detection_requests.id',ondelete='CASCADE'), nullable=False, index=True)
    class_name: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    bbox_x1: Mapped[float] = mapped_column(Float, nullable=False)
    bbox_y1: Mapped[float] = mapped_column(Float, nullable=False)
    bbox_x2: Mapped[float] = mapped_column(Float, nullable=False)
    bbox_y2: Mapped[float] = mapped_column(Float, nullable=False)

    request:Mapped[DetectionRequest] = relationship(back_populates='detections')