from fastapi import FastAPI
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi import _rate_limit_exceeded_handler

from database import engine, Base, Sessionmaker
from models.detection import DetectionRequest, Detection  # 테이블 등록을 위해 명시적으로 import 필요
from models.audit import AuditLog  # 감사 로그 테이블도 동일한 이유로 명시적 import
from models.user import User  # JWT 로그인용 사용자 테이블도 동일한 이유로 명시적 import
from routers import health, model, predict, metrics, training, auth
from middleware.audit_log import register_audit_middleware
from core.limiter import limiter
from services.user_service import seed_default_admin

# 앱 시작 시 테이블이 없으면 자동 생성
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AegisVision Drone Detection API")

# Rate Limiting (slowapi) 등록
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# 모든 요청/응답을 audit_logs 테이블에 기록
register_audit_middleware(app)


@app.on_event("startup")
def create_default_admin():
    # 최초 기동 시 관리자 계정이 없으면 .env의 DEFAULT_ADMIN_USERNAME/PASSWORD로 1개 생성
    db = Sessionmaker()
    try:
        seed_default_admin(db)
    finally:
        db.close()


@app.get("/")
def root():
    return {"message": "AegisVision Drone Detection API"}

app.include_router(auth.router)
app.include_router(health.router)
app.include_router(model.router)
app.include_router(predict.router)
app.include_router(metrics.router)
app.include_router(training.router)
