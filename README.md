# 🛰️ AegisVision — 드론 탐지 MLOps 파이프라인

드론(안티드론) 객체 탐지 모델을 학습부터 배포·모니터링까지 자동화된 파이프라인으로 구축한 MLOps 포트폴리오 프로젝트입니다. 단순히 모델을 학습시키는 데서 그치지 않고, 학습 → 실험 추적 → API 서빙 → 데이터베이스 로깅 → 인증/보안 → 컨테이너화 → CI/CD까지 실제 운영 가능한 시스템 형태로 구현하는 것을 목표로 했습니다.

## 프로젝트 배경

- 로봇공학 전공, 방산 분야를 1순위 희망 직종으로 두고 로봇 관련 직종도 함께 고려하며 진행한 포트폴리오 프로젝트
- 방산·보안 업계에서 실제로 다뤄지는 "안티드론(counter-drone) 탐지" 주제를 선택해 도메인 관련성을 확보
- YOLO, MLflow, FastAPI, PostgreSQL, Docker를 활용하여 약 한 달간 단계적으로 학습하며 구현
- 학습 과정에서 겪은 문제와 해결 과정을 아래 트러블슈팅 섹션에 상세히 기록

## 기술 스택

| 영역 | 기술 |
|---|---|
| 객체 탐지 모델 | YOLO (Ultralytics) |
| 실험 관리 | MLflow |
| 백엔드 API | FastAPI |
| 데이터베이스 | PostgreSQL + SQLAlchemy ORM |
| 프론트엔드 대시보드 | React + TypeScript (Vite), Tailwind CSS v4, shadcn/ui, recharts, nginx |
| (구) 대시보드 | Streamlit (React로 대체, 참고용으로 코드 유지) |
| 인증 | API Key (X-API-Key), JWT (관리자 로그인) |
| Rate Limiting | slowapi |
| 컨테이너화 | Docker, Docker Compose |
| 리버스 프록시 / HTTPS | Caddy |
| CI/CD | GitHub Actions |
| 테스트 | pytest |
| 패키지 관리 | uv |
| GPU 가속 | CUDA (RTX 3070) |

## 아키텍처

```
브라우저 ──▶ web (nginx, :8080) ──┬─▶ React 빌드 결과(정적 파일) 서빙
                                  └─▶ /api/*  ──▶ api (FastAPI, :8000, 내부 전용)
                                                      │
                          ┌───────────────────────────┼───────────────────────┐
                    ┌─────▼─────┐              ┌──────▼──────┐          ┌─────▼─────┐
                    │   YOLO    │              │ PostgreSQL  │          │  MLflow   │
                    │ (모델 추론)│              │(탐지/감사 로그)│          │(학습 이력) │
                    └───────────┘              └─────────────┘          └───────────┘

(운영 배포 시에는 Caddy가 앞단에서 HTTPS를 처리하도록 구성 가능 - docker-compose.yml에 주석으로 포함)
```

- 브라우저는 **8080 포트 하나**만 접근합니다. 백엔드(8000)는 호스트에 열지 않고, nginx가 `/api/` 요청만 `api` 컨테이너로 전달합니다.
- 화면과 API가 같은 주소(출처)로 보이므로 배포 환경에서는 CORS 설정이 필요 없습니다.

FastAPI는 라우터(`routers/`) · 스키마(`schemas/`) · 서비스(`services/`) · 모델(`models/`) 레이어로 분리된 구조로 설계했습니다.

| 레이어 | 역할 |
|---|---|
| `database.py` | DB 연결 설정 (engine, SessionLocal, Base) |
| `models/` | DB 테이블 구조 정의 (SQLAlchemy ORM) |
| `schemas/` | API 요청/응답 데이터 형태 정의 (Pydantic) |
| `services/` | 실제 비즈니스 로직 (YOLO 추론, DB 저장, MLflow 조회, 위협도 판정 등) |
| `routers/` | 엔드포인트 정의, 요청을 받아 서비스에 위임 |
| `core/` | 인증(API Key, JWT), Rate limiting 설정 |
| `middleware/` | 감사 로그(audit log) 미들웨어 |
| `scripts/` | 사람이 수동으로 실행하는 평가/병합용 스크립트 |

## 프로젝트 진행 과정

### 1. 데이터셋 & 모델 학습

- Roboflow Universe의 "Drone Detection data set" (단일 클래스, 약 3.3k 이미지)으로 시작
- YOLO(ultralytics)를 사전학습 가중치 기반 전이학습 방식으로 학습
- 학습이 여러 컴퓨터·여러 세션에 걸쳐 나뉘어 진행되었으며(약 13 → 5 → 10 → 40 epoch 등), 각 세션의 가중치(`last.pt`)를 이어받아 누적 학습
- 단일 클래스 모델 성능: mAP50 약 0.93, precision 약 0.91, recall 약 0.90
- 오탐(강아지를 드론으로 오인) 사례를 확인하고, Airplane/Bird/Drone/Helicopter 4클래스 데이터셋(Roboflow Universe)으로 확장
- CPU 학습(epoch당 약 25분)의 한계를 GPU(RTX 3070, CUDA) 전환으로 해결, 다중 클래스 모델 최종 성능: mAP50 약 0.99, precision 약 0.97, recall 약 0.97

### 2. 실험 추적 (MLflow)

- 학습마다 epochs, imgsz 등 하이퍼파라미터와 mAP50 · precision · recall · mAP50-95 지표를 MLflow에 기록
- 여러 세션에 걸쳐 나뉜 학습 기록을 하나의 누적(cumulative) 곡선으로 병합하는 스크립트 작성
- 단일 클래스와 다중 클래스 실험을 별도 계열로 구분해, 두 모델의 성능 향상 추이를 한 그래프에서 비교
- FastAPI의 `/model/training-history` 엔드포인트에서 이 기록을 조회해, 목표 epoch 수와 실제 완료된 epoch 수를 구분해 제공

### 3. API 서빙 (FastAPI)

| Method | Endpoint | 설명 |
|---|---|---|
| POST | `/predict` | 이미지 업로드 → 탐지 결과를 JSON으로 반환 |
| POST | `/predict/visualize` | 이미지 업로드 → 바운딩 박스가 그려진 결과 이미지 반환 |
| POST | `/predict/video` | 비디오 업로드 → 프레임별 탐지, 결과 영상과 요약 통계 반환 |
| GET | `/health` | 서버·모델 상태 확인 (인증 불필요, healthcheck용) |
| GET | `/model/info` | 현재 서빙 중인 모델의 경로·클래스 정보 |
| GET | `/metrics` | 총 요청 수, 평균 confidence, 평균 추론 시간 등 운영 지표 |
| GET | `/metrics/defense` | 방산 스타일 성능 지표 (낮은 오탐율에서의 Recall, FPS, 클래스별 탐지 분포) |
| GET | `/model/training-history` | MLflow 학습 이력 및 단일/다중 클래스 누적 성능 추이 |
| GET | `/alerts` | 위협 등급(threat_level)이 high/critical인 최근 탐지 목록 |
| POST | `/auth/login` | 관리자 로그인 (JWT 발급) |

`/model/load`, `/models`, `/model/current`처럼 MLflow Model Registry가 필요한 기능과 RTSP 실시간 스트림 처리는 난이도 대비 우선순위를 고려해 범위에서 제외했습니다.

### 4. 데이터베이스 (PostgreSQL)

- `detection_requests` / `detections` 1:N 구조로 설계해, 이미지 한 장에 여러 객체가 탐지되는 경우를 지원
- `detections`에 `threat_level` 컬럼을 추가해, 클래스와 confidence 기반으로 위협 등급(none/low/medium/high/critical)을 함께 저장
- `audit_logs` 테이블로 모든 API 요청(호출자, 경로, 상태 코드, 응답 시간)을 감사 로그로 기록, healthcheck 요청은 제외
- SQLAlchemy ORM(`Mapped`, `mapped_column`) 기반으로 테이블 정의

### 5. 경보 체계

- 클래스와 confidence를 조합한 규칙 기반 threat score 로직(`services/threat_service.py`) 구현
- 탐지 시마다 위협 등급을 계산해 DB에 함께 저장하고, `/alerts`로 고위험 탐지만 조회 가능하도록 구성
- 실시간 웹훅/이메일 알림까지는 범위를 좁혀, "탐지 → 위협 분류 → 조회 가능한 경보 목록"까지를 구현 범위로 확정

### 6. 방산 스타일 성능 지표

- 보안/국방 시스템 평가에서 흔히 쓰이는 지표로 평가 지표를 보강: 낮은 오탐율(precision 기준)에서의 Recall, 초당 처리 프레임(FPS)
- `scripts/evaluate_defense_metrics.py`로 오프라인에서 계산해 `defense_metrics.json`으로 저장, API가 이 파일을 읽어 응답
- 클래스별 탐지 분포(`class_distribution`)는 DB에 쌓인 실제 탐지 로그를 집계해 실시간으로 제공

### 7. 인증 & 보안

- API Key(`X-API-Key` 헤더) 인증을 `/predict`, `/model/info`, `/metrics`, `/metrics/defense`, `/model/training-history`, `/alerts`에 적용, `/health`와 `/auth/login`은 공개
- 업로드 파일은 확장자가 아닌 실제 파일 내용을 검증하고 크기 제한을 적용
- 관리자 로그인은 JWT 기반이며, 로그인 엔드포인트에는 slowapi로 요청 빈도 제한을 적용해 무차별 대입 공격을 방지
- 운영 환경에서는 Caddy가 HTTPS를 처리하고, FastAPI 포트는 외부에 직접 노출하지 않는 구조 (로컬 테스트 시에는 Caddy 없이 구성 가능)

### 8. 프론트엔드 대시보드 (React)

기존 Streamlit 대시보드를 **관제센터(NOC) 스타일의 React 대시보드**로 새로 만들었습니다. 백엔드는 그대로 두고 `frontend/` 폴더를 추가했습니다. (기술: React 19 + TypeScript + Vite, Tailwind CSS v4, shadcn/ui, lucide-react, recharts)

| 탭 | 기능 | 사용하는 API |
|---|---|---|
| 운영 대시보드 | 요청·탐지 수, 평균 신뢰도·추론 시간, 처리 속도, 엔드포인트별 요청/클래스별 탐지 차트 | `GET /metrics`, `GET /metrics/defense` |
| 경보 | 고위험 탐지 목록, 위협 등급별 색상 (10초마다 갱신) | `GET /alerts` |
| 객체 탐지 | 이미지 업로드 → 원본, 박스가 그려진 결과 이미지, 클래스별 신뢰도 막대 | `POST /predict`, `POST /predict/visualize` |
| 비디오 탐지 | 영상 업로드(최대 50MB) → 처리 경과 시간, 결과 영상 재생·다운로드, 프레임 요약 | `POST /predict/video` |
| 학습 이력 | 학습 실행 기록 표, 단일/다중 클래스 누적 학습 곡선 (mAP50 / mAP50-95 / precision / recall 선택) | `GET /model/training-history` |
| 모델 정보 | 모델 파일, 탐지 클래스 목록 | `GET /model/info` |

- 사이드바 하단에서 10초마다 `/health`를 호출해 **API 상태와 모델 로드 여부**를 표시합니다.
- API 호출은 `lib/api.ts`로, 주기적 갱신은 `lib/usePolling.ts` 커스텀 훅으로 공통화했습니다. (변하지 않는 값은 간격 0으로 한 번만 호출)
- 영상 탐지는 대시보드의 요청 수·평균 추론 시간에 포함하지 않습니다. 평균 추론 시간은 이미지 한 장 기준 지표인데 영상은 처리 시간이 훨씬 길어 평균이 왜곡되기 때문이며, 대신 영상 탭에서 자체 요약(총 프레임, 탐지 프레임 수, 클래스별 횟수)을 제공합니다. 대시보드 라벨도 "이미지 탐지 요청 수 / 이미지 탐지 수"로 명시했습니다.
- 기존 Streamlit 코드(`streamlit_app.py`, `Dockerfile.streamlit`)는 참고용으로 남겨두었으며 현재 `docker-compose.yml`에서는 사용하지 않습니다.

### 9. 컨테이너화 (Docker)

- `api`(FastAPI) · `db`(PostgreSQL) · `web`(React 빌드 + nginx) · `caddy`(리버스 프록시, 선택) 구성
- `web`은 멀티 스테이지 빌드: Node 이미지에서 `npm run build` → 결과물만 가벼운 nginx 이미지로 복사
- nginx가 `/api/` 요청을 `api:8000`으로 프록시 (업로드 최대 60MB, 프록시 대기 600초로 설정 - 기본값 1MB/60초면 이미지도 413, 긴 영상은 504로 실패)
- 모델 가중치(`runs/`), MLflow 기록(`mlflow.db`), 방산 지표(`defense_metrics.json`)는 volume으로 마운트해 코드와 분리 관리
- `docker-compose up --build` 한 번으로 전체 스택 기동 (`api`가 healthy가 된 뒤 `web`이 시작되도록 `depends_on: service_healthy` 적용)

### 10. CI/CD (GitHub Actions)

- push/PR 시 Docker 이미지 빌드 → PostgreSQL 서비스 컨테이너 기동 → API 컨테이너 기동 → `/health` 응답 대기 → 인증 로직(공개/401/200) 검증까지 자동 수행
- YOLO 모델 가중치는 CI 환경에 없으므로, 실제 추론(`/predict`)이 아닌 헬스체크와 인증 로직 검증을 CI 범위로 한정

### 11. 테스트 (pytest)

- `TestClient`를 `with` 컨텍스트로 사용해 FastAPI의 `lifespan`(관리자 계정 자동 생성 등)이 실제로 실행되도록 구성
- 운영 DB에 영향을 주지 않도록 테스트 전용 SQLite DB(`test.db`)를 사용
- `/health` 공개 여부, API Key 인증(401/200), 입력 검증(422), JWT 로그인 성공/실패 등 10개 테스트로 핵심 동작 검증
- CI 워크플로우에 통합해 push마다 자동 실행

## 실행 방법

### A. Docker로 전체 실행 (권장)

```bash
# 1. 환경 변수 파일 만들기 (예시 파일을 복사)
cp .env.example .env
# .env 안의 CHANGE_ME_ 값을 모두 직접 만든 값으로 교체합니다. (키 생성 예: openssl rand -hex 24)
grep -n "CHANGE_ME" .env        # 아무것도 출력되지 않으면 모두 교체된 것

# 2. 전체 스택 기동 (반드시 프로젝트 루트에서 실행)
docker-compose up --build -d
docker-compose ps               # api, db는 healthy, web은 Up

# 3. 확인
# React 대시보드: http://localhost:8080
```

`.env`에 들어가는 항목:

```dotenv
POSTGRES_DB=AegisVision
POSTGRES_USER=postgres
POSTGRES_PASSWORD=실제_비밀번호
DATABASE_URL=postgresql+psycopg2://postgres:실제_비밀번호@db:5432/AegisVision

# 서버가 허용하는 키 목록: "키=클라이언트이름"을 콤마로 연결 (공백 없음)
API_KEYS=<streamlit키>=streamlit-dashboard,<react키>=react-dashboard
STREAMLIT_API_KEY=<streamlit키>     # API_KEYS에 등록된 키와 동일
REACT_API_KEY=<react키>             # API_KEYS에 등록된 키와 동일, React 빌드 시 화면 코드에 포함

DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_PASSWORD=실제_비밀번호

JWT_SECRET_KEY=랜덤으로_생성한_긴_문자열
JWT_EXPIRE_MINUTES=60

DOMAIN=example.duckdns.org          # 실제 도메인 배포 시에만 필요
```

- 클라이언트(Streamlit/React)마다 키를 따로 발급해 서버 허용 목록(`API_KEYS`)에 등록합니다. 감사 로그(`audit_logs`)에서 **어느 화면이 호출했는지** 구분할 수 있습니다.
- `VITE_`로 시작하는 값은 **빌드 시점에 화면 코드에 고정**됩니다. `.env`의 키를 바꾸면 `docker-compose up --build -d`로 `web`을 다시 빌드하고, 브라우저는 `Ctrl+F5`로 새로고침하세요.

### B. 로컬 개발 (프론트엔드 수정 시)

터미널 2개를 사용합니다. Node 20.19 이상이 필요합니다.

| 터미널 | 폴더 | 명령 |
|---|---|---|
| 백엔드 | 프로젝트 루트 | `docker-compose up -d db` 후 `uv run uvicorn main:app --reload` |
| 프론트 | `frontend/` | `cp .env.local.example .env.local` → `npm install` → `npm run dev` |

접속: http://localhost:5173 (개발 모드는 백엔드 8000 포트에 직접 연결하며, 백엔드 CORS가 5173을 허용하도록 설정되어 있습니다)

- `frontend/.env.local`의 `VITE_API_KEY`는 서버 `API_KEYS`에 등록된 키여야 합니다. 수정하면 `npm run dev`를 껐다 켜야 반영됩니다.
- `npm` 명령은 `frontend/`에서, `docker-compose` 명령은 프로젝트 루트에서 실행합니다.
- 다른 컴퓨터에서 이어서 작업할 때는 `git pull` → `cd frontend` → `npm install` 후, 그 컴퓨터 백엔드의 키로 `.env.local`을 새로 만듭니다. (`.env`, `.env.local`은 git에 올라가지 않습니다)

### C. 테스트만 실행

```bash
uv sync
uv run pytest -v
```

## 주요 트러블슈팅

프로젝트 진행 중 겪은 문제와 해결 과정입니다.

### 1. 여러 컴퓨터에서 이어서 학습할 때 접근 권한이 없어 에러
- **시도**: 학원 컴퓨터로 학습을 시작하고, 집 컴퓨터에서 `resume=True`로 이어서 돌림
- **문제점**: `PermissionError`로 실패
- **원인**: `resume=True`는 이전 학습 시 `args.yaml`에 저장된 절대경로를 그대로 재사용하기 때문에 계정이 바뀌면 그 경로에 접근 권한이 없어 에러 발생
- **해결방법**: `resume=True` 대신, 이전 학습의 가중치 파일 `last.pt`를 새 학습의 시작점으로 불러오는 방식으로 전환

### 2. 결과 저장 경로가 예상과 다른 곳에 쌓임
- **시도**: 저장 경로를 명시하기 위해 `model.train(..., project="runs/detect", name="train")`으로 지정
- **문제점**: 결과가 `runs/detect/train`이 아니라 `runs/detect/runs/detect/train`처럼 폴더가 이중으로 생성됨
- **원인**: Ultralytics는 detect 작업 시 기본 저장 경로가 이미 `runs/detect`인데, `project="runs/detect"`를 추가로 지정해 경로가 중복됨
- **해결방법**: `project` 인자를 빼고 `name="train"`, `exist_ok=True`만 사용. 잘못된 경로에 쌓인 파일은 수정 시각을 비교해 최신 것을 정상 경로로 옮기고 잘못된 폴더는 삭제

### 3. DB 세션의 생성과 종료를 직접 관리하면서 발생할 수 있는 문제
- **시도**: FastAPI의 각 API에서 SQLAlchemy Session을 사용해 PostgreSQL에 데이터를 저장
- **문제점**: API 요청마다 DB Session을 생성 후 종료해야 하는데, 각 라우터에서 직접 관리해 예외 발생 시 Session이 정상적으로 정리되지 않음
- **원인**: DB Session의 생성과 종료에 대한 공통 관리 구조가 없었음
- **해결방법**: DB 세션 생성과 정리를 하나의 Dependency로 분리하고, `routers`에서 `Depends()`로 Session을 주입받아 요청이 끝나면 `finally`에서 자동 정리되도록 구성

### 4. 하나의 요청에 대한 DB 데이터가 부분적으로 저장됨
- **시도**: 하나의 이미지 요청에 대한 `DetectionRequest`와 여러 개의 `Detection` 데이터를 PostgreSQL에 저장
- **문제점**: 하나의 요청에 대한 DB 데이터가 부분적으로만 저장됨
- **원인**: `DetectionRequest`를 저장하고 `commit`한 다음 `Detection` 데이터를 추가로 저장하는 방식이라, 중간에 실패하면 반쪽짜리 데이터가 남음
- **해결방법**: `commit` 대신 `flush`를 사용하고, 저장 과정에서 오류가 발생하면 `rollback()`하도록 구성해 하나의 트랜잭션으로 묶음

### 5. 부모 데이터 삭제 시 Detection 데이터가 남는 문제
- **시도**: `DetectionRequest`와 `Detection`을 Foreign Key를 이용한 1:N 관계로 구성
- **문제점**: `DetectionRequest`가 삭제됐을 때 자식 데이터인 `Detection`이 남아 고아 데이터 발생
- **원인**: 부모/자식 데이터의 삭제 동작을 명시적으로 설정하지 않음
- **해결방법**: SQLAlchemy ORM에는 `cascade`, DB에는 Foreign Key에 `ON DELETE CASCADE` 적용

### 6. 모델 로딩과 추론 로직이 결합되는 문제
- **시도**: 추론 코드에서 YOLO 모델을 직접 불러와 객체 탐지를 수행
- **문제점**: 추론 로직이 모델 파일 경로와 로딩 방식까지 알고 있어, 모델이 변경될 때마다 추론 코드도 수정해야 함
- **원인**: 모델 관리·로딩 책임과 추론 책임이 하나의 코드에 섞여 있었음
- **해결방법**: 모델 로딩과 관리를 `ModelManager`로 분리하고, 추론 코드는 직접 모델을 생성하지 않고 `ModelManager`를 통해 가져오도록 구성

### 7. API 요청마다 YOLO 모델을 반복해서 로딩
- **시도**: `predict` 요청이 들어올 때마다 YOLO 모델을 생성해 추론
- **문제점**: 요청마다 모델을 새로 로딩하면 불필요한 초기화 시간이 반복 발생
- **원인**: 모델 객체의 생명주기를 관리하지 않고 요청 단위로 생성하는 구조였음
- **해결방법**: `ModelManager`에서 모델 객체를 한 번만 생성해 싱글턴처럼 유지하고, 이후 요청에서는 기존 객체를 재사용하도록 구성

### 8. 객체 탐지 결과 이미지를 API 응답으로 반환
- **시도**: `/predict/visualize`에서 바운딩 박스가 표시된 이미지를 반환
- **문제점**: `/predict`는 JSON을 반환하지만 `/predict/visualize`는 이미지 데이터를 반환해야 해서 동일한 응답 방식을 쓸 수 없음
- **원인**: API 목적에 따라 응답 데이터 형식이 다름
- **해결방법**: YOLO의 `result.plot()`으로 박스가 그려진 이미지를 생성해 `BytesIO`에 JPEG로 저장하고 `StreamingResponse`로 반환

### 9. FastAPI에서 DB 작업과 추론 로직의 책임 분리
- **시도**: `/predict` API에서 파일 업로드부터 YOLO 추론, 결과 파싱, DB 저장까지 한 번에 처리
- **문제점**: 하나의 라우터 함수에 여러 책임이 집중되어 코드가 복잡해지고 개별 수정·테스트가 어려움
- **원인**: 요청을 처리하는 라우터와 실제 비즈니스 로직이 분리되지 않았음
- **해결방법**: 추론(`services/inference.py`), DB 저장(`services/detection_service.py`)으로 기능별 책임을 분리

### 10. MLflow에 학습 기록이 나타나지 않는 오류
- **시도**: `mlflow.set_tracking_uri("sqlite:///mlflow.db")`로 학습 스크립트에서 기록을 남기고, `mlflow ui`로 대시보드 확인
- **문제점**: `mlflow ui`를 옵션 없이 실행하면 기록한 실험이 안 보이고 "Default"만 뜸
- **원인**: `mlflow ui`를 인자 없이 실행하면 기본 저장소(`mlruns/` 폴더)를 보여주는데, 실제 기록은 `mlflow.db`(SQLite)에 쌓이고 있어 서로 다른 곳을 보고 있었음
- **해결방법**: `mlflow ui --backend-store-uri sqlite:///mlflow.db`처럼 실제 기록 위치를 명시해서 실행

### 11. 컬럼 구조를 바꿔도 테이블이 갱신되지 않는 문제
- **시도**: 모델 파일에 정의한 테이블 구조를 `Base.metadata.create_all(bind=engine)`으로 PostgreSQL에 생성
- **문제점**: 컬럼명을 바꾼 뒤에도 "테이블이 존재하지 않는다"는 에러가 계속 발생
- **원인**: `create_all()`은 테이블이 "없을 때만" 생성해주는 함수라, 컬럼 구조를 바꿔도 이미 만들어진 테이블에는 반영이 안 됨
- **해결방법**: 테이블을 `DROP TABLE`로 지운 뒤, 서버를 완전히 종료했다가 처음부터 재시작해 최신 스키마로 재생성

### 12. 목표 epoch 수를 기준으로 계산해 누적 그래프가 부풀려짐
- **시도**: 여러 학습 세션(run)의 mAP50 등 지표를 하나의 누적 그래프로 이어붙이는 스크립트 작성, `run.data.params.get("epochs")`(목표 epoch 값)를 기준으로 각 run의 step offset을 계산
- **문제점**: 실제로는 약 68 epoch 진행했는데, 병합된 그래프의 총 step 수가 97까지 나오는 등 실제보다 부풀려짐
- **원인**: 지표 기록이 아예 없는 run이나 patience로 조기 종료된 run까지 "목표로 설정한 epochs 파라미터" 값만큼 offset을 채워 넣어, 실제로 진행되지 않은 구간까지 누적 길이에 포함됨
- **해결방법**: 목표 epochs 파라미터 대신, 각 run에서 실제로 기록된 metric history의 마지막 step만을 기준으로 offset을 계산하도록 수정. 지표 기록이 전혀 없는 run은 건너뜀

### 13. 전체 합계가 항상 0으로 나옴
- **시도**: `/model/training-history` API에서 각 run의 실제 완료 epoch(`actual_epochs`)를 별도 계산해 응답에 추가하고, 전체 합계(`total_epochs`)도 실제값 기준으로 산출
- **문제점**: `actual_epochs` 필드는 정상적으로 나왔지만, 목표값과 실제값이 섞여 나오고 `total_epochs`는 항상 0
- **원인**: 실제값을 목표값 변수에 누적시키고, 정작 전체 합계를 누적해야 할 변수에는 더하는 코드 자체가 빠져 있었음
- **해결방법**: 목표값과 실제값을 각각 독립된 변수로 유지하고, 전체 합계에는 실제값만 정확히 누적되도록 로직 정리

### 14. uv의 전역 인덱스 설정이 프로젝트 전체 의존성 해석을 바꿔버림
- **시도**: GPU 버전 PyTorch를 설치하기 위해 `[[tool.uv.index]]`에 PyTorch 전용 인덱스를 `default = true`로 지정
- **문제점**: `torch`뿐 아니라 `bcrypt`, `altair` 등 전혀 관계없는 패키지들까지 "레지스트리에서 찾을 수 없다"는 에러가 반복적으로 발생
- **원인**: `default = true`로 설정하면 프로젝트의 기본 패키지 저장소 자체가 PyPI에서 PyTorch 전용 인덱스로 바뀌어버려, 다른 모든 패키지도 그 인덱스에서만 찾으려 함
- **해결방법**: `default = true` 대신 `explicit = true`로 바꾸고, `[tool.uv.sources]`에서 `torch`/`torchvision`에만 해당 인덱스를 명시적으로 지정해 나머지 패키지는 정상적으로 PyPI를 사용하도록 분리

### 15. 로컬 환경과 Docker 환경의 DB가 분리되어 스키마가 어긋남
- **시도**: 로컬 PostgreSQL에서 `threat_level` 컬럼을 추가하고 테이블을 재생성한 뒤, Docker 컨테이너에서 동일 기능을 테스트
- **문제점**: Docker 환경에서도 동일하게 "`threat_level` 컬럼이 존재하지 않는다"는 에러 발생
- **원인**: Docker의 PostgreSQL은 `pgdata`라는 별도 볼륨을 사용하는, 로컬 PostgreSQL과 완전히 독립된 데이터베이스였음
- **해결방법**: `docker-compose down -v`로 Docker 전용 볼륨을 초기화한 뒤 재기동해, 최신 스키마로 테이블을 다시 생성

### 16. 환경변수를 로드하는 코드가 없어 인증이 전부 실패함
- **시도**: `.env`에 API 키, JWT 비밀키 등을 설정하고 서버 실행
- **문제점**: 올바른 API 키를 헤더에 담아 보내도 계속 401 Unauthorized가 발생
- **원인**: `main.py`를 비롯한 어떤 파일에도 `load_dotenv()` 호출이 없어, `.env` 파일의 값이 애초에 환경변수로 로드되지 않고 있었음
- **해결방법**: `main.py` 최상단, 다른 모듈을 import하기 전에 `load_dotenv()`를 호출하도록 추가

### 17. pytest의 TestClient가 시작 이벤트를 실행하지 않는 문제
- **시도**: `TestClient(app)`으로 FastAPI 테스트 클라이언트를 만들어 로그인 엔드포인트 테스트
- **문제점**: 올바른 비밀번호로 로그인해도 계속 401 Unauthorized
- **원인**: `TestClient(app)`을 `with` 블록 없이 그냥 생성하면 FastAPI의 `lifespan`(앱 시작 시 실행되는 이벤트, 여기서는 관리자 계정 자동 생성)이 실행되지 않아 DB에 관리자 계정 자체가 없었음
- **해결방법**: `with TestClient(app) as c:` 형태로 컨텍스트 매니저를 사용해 lifespan이 실제로 실행되도록 pytest fixture 구성. 운영 DB에 영향을 주지 않도록 테스트 전용 SQLite DB도 함께 분리

### 18. 다중 클래스 학습 기록에 지표가 한 지점만 남음
- **시도**: 다중 클래스(4종) 모델 학습 후, 단일 클래스와 동일하게 누적 학습 곡선을 그래프로 표시
- **문제점**: 단일 클래스는 여러 지점을 잇는 꺾은선 그래프로 나오는데, 다중 클래스는 점 하나만 찍힘
- **원인**: FastAPI 개발 중 MLflow가 중복으로 로그를 남기는 문제를 해결하기 위해 Ultralytics의 자동 epoch별 로깅(`yolo settings mlflow=False`)을 꺼둔 상태로 다중 클래스를 학습해, 직접 기록한 최종 성능 1개 지점만 남게 됨
- **해결방법**: 자동 로깅을 다시 켜고(`yolo settings mlflow=True`), 사전학습 가중치부터 다시 학습을 진행해 epoch별 지표가 촘촘히 기록되도록 재학습

### 19. 클래스 수가 다른 모델은 기존 가중치에서 이어받을 수 없음
- **시도**: 단일 클래스로 학습된 가중치(`best.pt`)를 이어받아 다중 클래스(4종) 데이터로 추가 학습 시도
- **문제점**: 학습이 의도대로 진행되지 않거나 오류 발생
- **원인**: YOLO 모델의 출력층 구조는 클래스 수에 따라 고정되는데, 클래스 수가 다른 가중치는 구조 자체가 맞지 않아 이어받기가 불가능함
- **해결방법**: 클래스 수가 바뀌는 경우 사전학습 원본(`yolo26n.pt`)부터 새로 전이학습을 시작하도록 전환

### 20. 결과 비디오가 브라우저에서 재생되지 않음
- **시도**: OpenCV로 프레임별 탐지 결과를 합성한 비디오 파일을 `/predict/video`로 반환
- **문제점**: 응답받은 비디오가 Streamlit의 `st.video()`에서 재생되지 않고 검은 화면만 나옴
- **원인**: OpenCV 기본 코덱(`mp4v`)으로 인코딩된 영상이 대부분의 웹 브라우저(HTML5 video)와 호환되지 않음
- **해결방법**: 코덱을 브라우저 호환성이 좋은 `avc1`(H.264)로 변경

### 21. 화면에서는 "API 연결 실패"인데 curl은 정상 (CORS)
- **시도**: React 개발 서버(`localhost:5173`)에서 백엔드(`localhost:8000`)의 API 호출
- **문제점**: 터미널의 curl은 성공하는데 브라우저에서는 요청이 막혀 "API 연결 실패"가 표시됨
- **원인**: 화면(5173)과 API(8000)의 포트가 달라 브라우저가 서로 다른 출처로 보고 CORS 정책으로 차단. curl에는 이 정책이 없음. 또한 영상 요약을 담은 커스텀 헤더(`X-Detection-Summary`)는 서버가 노출을 허용하지 않으면 화면 코드에서 읽을 수 없음
- **해결방법**: 백엔드에 `CORSMiddleware`를 추가해 5173 출처를 허용하고 `expose_headers=["X-Detection-Summary"]` 설정. 에러 응답에도 CORS 헤더가 붙도록 다른 미들웨어보다 나중에(가장 바깥에) 추가. Docker 배포에서는 nginx `/api` 프록시로 같은 출처가 되어 CORS가 필요 없음

### 22. shadcn/ui 초기화 실패 (경로 별칭 · Tailwind 설정 인식 불가)
- **시도**: `npx shadcn init`으로 UI 컴포넌트 라이브러리 설치
- **문제점**: "No import alias found", "No Tailwind CSS configuration found" 오류
- **원인**: shadcn은 `tsconfig`의 `paths`(`@/*` 별칭)와 CSS 파일의 `@import "tailwindcss"`를 보고 프로젝트를 판단하는데, 둘 다 설정되어 있지 않았음. 또한 최신 TypeScript에서는 `baseUrl`이 deprecated 되어 경고 발생
- **해결방법**: `tsconfig.json`과 `tsconfig.app.json`에 `paths` 추가(`baseUrl`은 제거), `vite.config.ts`에 동일한 `@` 별칭 추가, `index.css`에 `@import "tailwindcss"` 추가 후 재실행

### 23. 다른 컴퓨터에서 curl이 실패하고 React가 401을 반환
- **시도**: 집과 학원 컴퓨터를 오가며 같은 프로젝트에서 작업
- **문제점**: 한 컴퓨터에서는 되던 API 호출이 다른 컴퓨터에서는 `Connection refused`, JSON 파싱 오류, 401로 실패
- **원인**: (1) 그 컴퓨터에서 백엔드가 실행 중이지 않았음 (2) `.env`와 `frontend/.env.local`은 git에 올라가지 않아 컴퓨터마다 따로 있고, 컴퓨터마다 서버의 API 키가 달랐음
- **해결방법**: 백엔드를 먼저 기동(필요 시 `docker-compose up -d db`)하고, 그 컴퓨터 `.env`의 `API_KEYS`에 등록된 키로 `frontend/.env.local`을 새로 작성. 키가 맞는지는 값을 출력하지 않고 상태 코드만 확인
  ```bash
  key=$(grep '^REACT_API_KEY=' .env | cut -d= -f2- | tr -d '\r')
  curl -s -o /dev/null -w "HTTP %{http_code}\n" -H "X-API-Key: $key" http://localhost:8080/api/metrics
  ```

### 24. Docker의 web 컨테이너가 nginx 대신 Streamlit을 실행하려 함
- **시도**: 기존 `web`(Streamlit) 서비스 정의를 React/nginx 이미지로 교체
- **문제점**: 이미지를 바꿨는데도 컨테이너가 정상 기동하지 않음
- **원인**: compose의 `command`는 이미지의 기본 실행 명령(nginx)을 덮어쓰는데, 이전 Streamlit용 `command`/`environment`가 남아 있었음
- **해결방법**: `web` 서비스에서 `command`, `environment`를 삭제하고 `build`(context·args), `ports: 8080:80`, `depends_on`만 남김

### 25. `frontend/` 폴더에서 docker-compose를 실행해 환경 변수가 비어 있음
- **시도**: 프론트엔드 폴더에서 `docker-compose up --build` 실행
- **문제점**: `${REACT_API_KEY}` 같은 값이 빈 문자열로 치환되어 빌드가 의도와 다르게 동작
- **원인**: compose는 실행한 위치(프로젝트 디렉터리)의 `.env`를 읽어 변수를 치환하는데, `.env`는 프로젝트 루트에만 있음
- **해결방법**: `docker-compose`는 항상 프로젝트 루트에서 실행

### 26. 키를 바꿨는데도 화면에서 계속 401
- **시도**: `.env`의 `REACT_API_KEY`를 수정하고 컨테이너만 재시작
- **문제점**: 대시보드에 "지표를 불러오지 못했습니다(HTTP 401)" 표시
- **원인**: Vite의 `VITE_*` 환경 변수는 서버 실행 시점이 아니라 **빌드 시점**에 번들 코드에 문자열로 박힘. 컨테이너 재시작만으로는 이미 빌드된 코드의 키가 바뀌지 않음. 또한 `.env` 키가 서버 `API_KEYS`에 등록되어 있지 않아도 401
- **해결방법**: `REACT_API_KEY`가 `API_KEYS`에 `키=이름` 형태로 등록되어 있는지 확인한 뒤 `docker-compose up --build -d`로 `web` 재빌드, 브라우저는 `Ctrl+F5`

### 27. Docker 빌드가 TypeScript 오류로 실패
- **시도**: `docker-compose up --build`로 React 이미지 빌드
- **문제점**: 로컬 `npm run dev`에서는 잘 보이던 코드가 Docker 빌드 단계에서 실패
- **원인**: 빌드 명령(`npm run build` = `tsc -b && vite build`)은 개발 서버보다 타입 검사가 엄격해, 타입으로만 쓰는 import(`import type` 필요), 사용하지 않는 변수 등이 오류가 됨
- **해결방법**: 이미지를 빌드하기 전에 `frontend/`에서 `npm run build`를 먼저 실행해 오류를 로컬에서 잡음

### 28. 업로드 413 오류, 긴 영상 처리 시 504 오류
- **시도**: nginx 프록시를 거쳐 이미지·영상을 업로드
- **문제점**: 1MB가 넘는 파일은 `413`, 처리에 60초가 넘는 영상은 `504`로 실패
- **원인**: nginx 기본값이 요청 본문 최대 1MB, 프록시 응답 대기 60초
- **해결방법**: `nginx.conf`에 `client_max_body_size 60m`, `proxy_read_timeout 600s`, `proxy_send_timeout 600s` 설정

### 29. 영상 탐지 후에도 대시보드의 총 요청 수가 늘지 않음
- **시도**: 영상 탐지를 실행한 뒤 대시보드의 "총 요청 수" 확인
- **문제점**: 영상을 처리해도 숫자가 그대로
- **원인**: `/metrics`는 `detection_requests` 테이블의 행을 집계하는데, 영상 엔드포인트는 해당 테이블에 기록하지 않는 설계. 영상까지 기록하면 이미지 한 장 기준인 평균 추론 시간이 왜곡됨
- **해결방법**: 설계를 유지하고 대시보드 라벨을 "이미지 탐지 요청 수 / 이미지 탐지 수"로 변경해 의미를 명확히 함

### 30. Helicopter 위협 등급이 한 단계 낮게 나옴
- **시도**: 헬리콥터를 높은 신뢰도로 탐지해 경보 등급 확인
- **문제점**: 규칙상 나와야 할 등급보다 한 단계 낮게 판정됨
- **원인**: 모델이 내보내는 클래스명은 `Helicopter`(대문자 시작)인데, 위협 규칙 딕셔너리의 키는 소문자였음. 딕셔너리 조회는 대소문자를 구분하므로 규칙을 찾지 못하고 기본값으로 처리됨
- **해결방법**: 규칙 키를 `"Helicopter"`로 수정. 이미 저장된 과거 경보는 저장 당시 등급을 유지하므로 새 탐지부터 반영됨

## 향후 개선 방향 (Future Work)

- **실시간 스트림 처리**: RTSP/웹캠 입력을 받아 WebSocket 기반으로 실시간 프레임을 처리하고, ByteTrack 등으로 프레임 간 객체 추적(tracking)까지 지원하는 구조로 확장
- **실제 도메인 배포**: 현재 Caddy + 리버스 프록시 구조는 준비되어 있으나, 실제 도메인을 연결한 라이브 배포는 아직 진행하지 않음
- **MLflow Model Registry 연동**: 현재 모델 경로를 코드에 직접 지정하는 방식을 Model Registry 기반의 버전 관리·배포 방식으로 전환
- **API 키를 화면 코드에서 제거**: 현재 `VITE_API_KEY`는 빌드 결과물에 포함되어 브라우저 개발자 도구로 볼 수 있습니다. 시연용으로는 충분하지만, 실서비스라면 이미 구현된 JWT 로그인(`/auth/login`)을 화면에 연결해 키를 화면에 두지 않는 구조로 전환해야 합니다.
- **프론트엔드 개선**: 영상 처리 중 탭을 이동해도 결과가 유지되도록 상태를 상위로 올리기, 학습 곡선 스무딩/세션 경계 표시, 서버가 그린 이미지 대신 bbox 좌표로 브라우저에서 박스 그리기, 영상 결과 임시 파일 자동 삭제
- **웹훅/이메일 알림**: 현재 경보 체계는 조회(`/alerts`) 방식이며, 고위험 탐지 발생 시 외부로 실시간 알림을 보내는 기능은 범위에서 제외

## 프로젝트 구조

```
AegisVision/
├── core/                   # 인증(API Key, JWT), Rate limiting
│   ├── security.py
│   └── limiter.py
├── middleware/
│   └── audit_log.py        # 요청/응답 감사 로그
├── models/                 # SQLAlchemy ORM 테이블 정의
│   ├── detection.py
│   ├── audit.py
│   └── user.py
├── routers/                # API 엔드포인트
│   ├── health.py
│   ├── model.py
│   ├── predict.py
│   ├── metrics.py
│   ├── defense_metrics.py
│   ├── training.py
│   ├── alerts.py
│   └── auth.py
├── schemas/                # Pydantic 요청/응답 스키마
│   ├── prediction.py
│   ├── model.py
│   ├── training.py
│   └── auth.py
├── services/                # 비즈니스 로직
│   ├── inference.py
│   ├── model_manager.py
│   ├── detection_service.py
│   ├── training_service.py
│   ├── threat_service.py
│   ├── metrics_service.py
│   ├── video_inference.py
│   ├── upload_validation.py
│   └── user_service.py
├── scripts/                 # 수동 실행용 평가/병합 스크립트
│   └── evaluate_defense_metrics.py
├── tests/                   # pytest 테스트
│   ├── conftest.py
│   └── test_api.py
├── .github/workflows/
│   └── ci.yml
├── runs/detect/              # 학습된 모델 가중치
├── main.py                   # FastAPI 진입점
├── database.py                # DB 연결 및 세션
├── streamlit_app.py            # (구) Streamlit 대시보드 - 참고용
├── multiclass_train.py          # 다중 클래스 학습 스크립트
├── resume_multiclass.py          # 다중 클래스 이어서 학습
├── drone_train.py                 # 단일 클래스 학습 스크립트 (초기 버전)
├── defense_metrics.json
├── mlflow.db
├── Dockerfile
├── Dockerfile.streamlit         # (구) Streamlit 이미지 - 현재 compose에서는 미사용
├── .env.example                 # 환경 변수 예시 (복사해서 .env 생성)
├── docker-compose.yml
├── Caddyfile
├── requirements.txt
├── requirements-streamlit.txt
├── pyproject.toml
├── uv.lock
├── frontend/                  # React 대시보드
│   ├── Dockerfile             # Node 빌드 → nginx 서빙 (멀티 스테이지)
│   ├── nginx.conf             # 정적 파일 + /api 프록시
│   ├── .env.local.example     # 로컬 개발용 환경 변수 예시
│   └── src/
│       ├── App.tsx            # 탭 → 화면 대응표
│       ├── pages/             # Dashboard, Alerts, Detect, Video, Training, ModelInfo
│       ├── components/        # Sidebar, ApiStatus, Stat, CountBarChart, TrainingChart, ui/
│       └── lib/               # api.ts(요청 함수), usePolling.ts(주기 호출 훅)
├── .gitignore
└── README.md
```