from fastapi import FastAPI, Depends
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi import _rate_limit_exceeded_handler

from database import engine, Base, Sessionmaker
from models.detection import DetectionRequest, Detection  # 테이블 등록을 위해 명시적으로 import 필요
from models.audit import AuditLog  # 감사 로그 테이블도 동일한 이유로 명시적 import
from models.user import User  # JWT 로그인용 사용자 테이블도 동일한 이유로 명시적 import
from routers import health, model, predict, metrics, training, auth, alerts, video, defense_metrics
from middleware.audit_log import register_audit_middleware
from core.limiter import limiter
from services.user_service import seed_default_admin
from core.security import verify_api_key, get_current_user
from contextlib import asynccontextmanager

# 앱 시작 시 테이블이 없으면 자동 생성
Base.metadata.create_all(bind=engine)




@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시 실행되는 부분 (기존 create_default_admin 내용)
    db = Sessionmaker()
    try:
        seed_default_admin(db)
    finally:
        db.close()
    
    yield  # 여기서부터 앱이 실제로 돌아가는 구간
    
    # 종료 시 실행하고 싶은 게 있다면 여기에 (지금은 없음)


app = FastAPI(title="AegisVision Drone Detection API", lifespan=lifespan)

# Rate Limiting (slowapi) 등록
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# 모든 요청/응답을 audit_logs 테이블에 기록
register_audit_middleware(app)


@app.get("/")
def root():
    return {"message": "AegisVision Drone Detection API"}



app.include_router(auth.router)
app.include_router(health.router)
app.include_router(model.router, dependencies=[Depends(verify_api_key)])
app.include_router(predict.router, dependencies=[Depends(verify_api_key)])
app.include_router(metrics.router, dependencies=[Depends(verify_api_key)])
app.include_router(training.router, dependencies=[Depends(verify_api_key)])
app.include_router(video.router, dependencies=[Depends(verify_api_key)])
app.include_router(alerts.router, dependencies=[Depends(verify_api_key)])
app.include_router(defense_metrics.router, dependencies=[Depends(verify_api_key)])
