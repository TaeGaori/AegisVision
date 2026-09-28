from fastapi import FastAPI,Depends

from database import engine, Base
from models.detection import DetectionRequest, Detection  # 테이블 등록을 위해 명시적으로 import 필요
from models.audit import AuditLog
from core.security import verify_api_key
from middleware.audit_log import register_audit_middleware
from routers import health, model, predict, metrics, training

# 앱 시작 시 테이블이 없으면 자동 생성
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AegisVision Drone Detection API")
register_audit_middleware(app)

@app.get("/")
def root():
    return {"message": "AegisVision Drone Detection API"}

auth = [Depends(verify_api_key)]

app.include_router(health.router)
app.include_router(model.router,dependencies=auth)
app.include_router(predict.router,dependencies=auth)
app.include_router(metrics.router,dependencies=auth)
app.include_router(training.router,dependencies=auth)

