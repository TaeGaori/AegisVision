# MLOps 포트폴리오 프로젝트 계획

## 프로젝트 주제
드론/CCTV 영상 기반 객체 탐지 MLOps 파이프라인

- 배경: 로봇공학부 전공, 1순위 희망 직종 방산 / 로봇 관련 직종도 함께 고려
- 목표: 모델 정확도보다 "데이터 → 학습 → 배포 → 모니터링"이 자동화된 파이프라인 구축에 집중
- 기간: 약 4주

## 기술 스택
- 모델: YOLOv8 (ultralytics) — 사전학습 모델 전이학습
- 실험 관리: MLflow
- 서빙: FastAPI
- 저장소: PostgreSQL (탐지 로그 저장)
- 컨테이너화: Docker, docker-compose
- CI/CD: GitHub Actions
- 모니터링: Streamlit (간단한 대시보드)

## 데이터 소스
- **메인 (Roboflow Universe)**: 드론/감시/객체탐지 관련 공개 데이터셋. 이미 라벨링 완료, YOLO 포맷으로 바로 다운로드 가능. 1주차부터 이 데이터로 베이스라인 파이프라인을 끝까지 완성
- **보조 (AI Hub)**: 국내 자율주행드론 비행 영상 데이터셋. 다운로드 승인 절차 필요(1주차 초반 미리 신청). 승인되면 기존 파이프라인에 데이터 소스로 추가해 재학습/검증 — 방산 지원 시 "국내 실데이터 검증" 포인트로 활용
- 구조: Roboflow가 기본 베이스, AI Hub는 옵션으로 얹는 방식 (승인이 늦어져도 전체 일정에 영향 없음)

## 4주 일정

### 1주차 — 학습 + 환경 세팅 + 데이터 확보
- 1~2일: YOLOv8 Quickstart 따라 하기 (설치, `yolo predict`/`yolo train` CLI로 감 잡기)
- 3일: MLflow Tracking Quickstart 따라 하기 (log_param, log_metric, MLflow UI 확인)
- 4일: Roboflow Universe에서 데이터셋 선택·다운로드 + AI Hub 데이터셋 다운로드 신청
- 5~7일: Roboflow 데이터로 YOLOv8 전이학습 1차 시도, MLflow 로깅 연동

### 2주차 — 모델 학습 + 실험 관리
- 데이터 증강, epoch/learning rate 등 바꿔가며 2회 정도 실험 반복 (실력 감안해 과도한 튜닝은 지양)
- AI Hub 데이터 승인됐다면 추가 데이터로 재학습/검증
- best 모델 선정 및 저장(.pt)

### 3주차 — 서빙 + 컨테이너화
- FastAPI에 `/predict` 엔드포인트 구현 (이미지 업로드 → 탐지 결과 반환)
- 탐지 로그(클래스, 좌표, confidence, 시각)를 PostgreSQL에 저장
- Docker + docker-compose로 FastAPI·PostgreSQL 컨테이너화, 로컬 end-to-end 테스트

### 4주차 — CI/CD + 모니터링 + 포트폴리오 정리
- 1~3일: GitHub Actions로 테스트→빌드→이미지 푸시 자동화 파이프라인 구성
- 4~5일: Streamlit으로 간단한 모니터링 대시보드 (탐지 건수, 모델 성능 추이)
- 6~7일: README·아키텍처 다이어그램 정리, 발표자료 준비

## 참고 튜토리얼 링크
- YOLOv8 Quickstart: https://docs.ultralytics.com/quickstart/
- MLflow Tracking Quickstart: https://mlflow.org/docs/latest/getting-started/intro-quickstart/
- Roboflow Universe: https://universe.roboflow.com
- AI Hub 자율주행드론 비행 영상 데이터: https://www.aihub.or.kr/aihubdata/data/view.do?currMenu=115&topMenu=100&dataSetSn=190
- GitHub Actions Quickstart: https://docs.github.com/en/actions/quickstart



---

## python 코드로 모델 로드 방법 익히기
```
model = YOLO("yolo26n.yaml")               # 빈 구조만 생성
model = YOLO("yolo26n.pt")                 # 사전학습 가중치 로드
model = YOLO("yolo26n.yaml").load("yolo26n.pt")  # 구조+가중치 결합
```

## 학습 실행
```
results = model.train(data="coco8.yaml", epochs=100, imgsz=640)
```
- 8장짜리 초소형 샘플 데이터셋으로 학습
- runs/detect/train 폴더에 저장된 confusion matrix, loss/성능 그래프(results.png) 읽는 법 학습

## 결과 해석
- `confusion matrix` : 왼쪽 위부터 오른쪽 아래로 대각선이 찐하면 정답, 벗어나면 오류 
- `loss/성능 그래프` : train loss는 계속 감소, val loss는 40 epoch 이후 오히려 증가하고 mAP도 급락 -> 과적합 val_loss가 올라가기 전에 멈추는 게 좋다는 판단 기준을 배움


- YOLO	: 실제로 "학습을 수행"하는 주체 — 이미지 넣고, 모델 돌리고, 성능 숫자를 뽑아냄
    - `python COCO8.py`로 실행
- MLflow :	YOLO가 만들어낸 결과(설정값 + 성능 숫자 + 가중치 파일)를 기록 저장소에 쌓아두고, 여러 번의 실험을 비교·추적하게 해주는 도구
    - `python MLflow.py` -> `mlflow ui --backend-store-uri sqlite:///mlflow.db`순서로 실행 (db형태로 저장이 되어서 이 코드로 실행)

---
1. Roboflow Universe에서 데이터 다운
2. YOLO로 학습(`python drone_train.py`)





---
# 트러블 슈팅
---
### 1. 여러 컴퓨터에서 이어서 학습할 때 접근 권한이 없어 에러
- **시도** : 학원 컴퓨터로 학습을 시작하고, 집 컴퓨터에서 `resume=True`로 이어서 돌림
- **문제점** : `PermissionError`로 실패
- **원인** : `resume=True`는 이전 학습 시 `args.yaml`에 저장된 절대경로를 그대로 재사용하기 때문에 계정이 바뀌면 그 경로에 접근 권한이 없어 에러 발생함
- **해결방법** : `resume=True`대신, 이전 학습의 가중치 파일 `last.pt`를 새 학습의 시작점으로 불러 오는 방식으로 변환 

---

### 2. 결과 저장 경로가 예상과 다른 곳에 쌓임
- **시도** : `python drone_train.py`로 `last.pt`를 시작점으로 가져와 학습 시작
- **문제점** : `runs/detect/train`안에 `runs/detect`폴더가 하나 더 생기고 새로 생긴 폴더에 학습 결과가 저장됨
- **원인** : ***Ultralytics***는 detect작업 시 기본 저장 경로가 이미 `runs/detct`인데 코드에 `project='runs/detect'`를 추가로 지정해 경로가 중복됨
- **해결방법** : `project='runs/detect'`인자를 빼고 name만 사용하고 `ls -l`로 파일 수정 시각을 비교해 최신 파일을 정상 경로로 `cp`한 뒤 잘못된 파일 삭제함

---

### 3. DB 세션의 생성과 종료를 직접 관리하면서 발생할 수 있는 문제
- **시도** :**FastAPI**의 각 API에서 SQLAlchemy Session을 사용하여 **PostgreSQL**에 데이터를 저장
- **문제점** : API 요청마다 DB Session을 생성 후 종료해야 하는데 각 라우터에서 직접 Session으로 관리하여 예외 발생 시 Session이 정상적으로 정리되지 않음
- **원인** : **DB** Session의 생성과 종료에 대한 공통적인 관리 구조가 없어 발생함
- **해결방법** : **DB** 세션 생성과 정리를 하나의 `Dependency`로 분리하고 `routers`에 `Depends()`를 사용해 Session을 주입하고 API 요청이 끝나면 `finally`에서 Session이 자동 정리되도록 구성

---

### 4. 하나의 요청에 대한 DB 데이터가 부분적으로 저장됨
- **시도** : 하나의 이미지 요청에 대한 `DetectionRequest`와 여러 개의 `Detection` 데이터를 **PostgreSQL**에 저장
- **문제점** : 하나의 요청에 대한 **DB** 데이터가 부분적으로 저장됨
- **원인** : `DetectionRequest`를 저장하고 `commit`한 다음 `Detection` 데이터를 추가로 저장하는 방식을 사용함
- **해결방법**  : `commit` 대신 `flush` 를 사용하고 저장 과정에서 오류가 발생하면 rollback()하도록 구성

---

### 5. 부모 데이터 삭제 시 Detection 데이터가 남는 문제
- **시도** : `DetectionRequest`와 `Detection`을 `Foreign Key`를 이용한 1:N 관계로 구성
- **문제점** : `DetectionRequest`가 삭제되었을 때 자식데이터인`Detection`가 남아 고아 데이터 발생 
- **원인** : 부모 데이터와 자식 데이터의 삭제 동작을 명시적으로 설정하지 않음
- **해결방법** : **SQLAlchemy ORM**에는 `cascae` **Database**에는 `Foreign Key`에 `ON DELETE CASCADE`적용

---

### 6. 모델 로딩과 추론 로직이 결홥되는 문제 
- **시도** : `inference.py`에서 YOLO 모델을 직접 불러와 객체 탐지를 수행
- **문제점** : 추론 로직에서 모델 파일의 경로와 로직 방식까지 알고 있어 모델이 변경될 때 추론 코드도 수정해야 하는 문제 발생
- **원인** : 모델의 관리 및 로딩 책임과 추론 책임이 하나의 코드에 있음
- **해결방법** : 모델의 로딩과 관리를 `ModelManager`로 분리하고 추론 코드에서는 직접 모델을 생성하지 않고 형태로 모델을 가져오도록 구성

---

### 7. API 오청마다 YOLO 모델을 반복해서 로딩
- **시도** : `predict` 요청이 들어올 때 YOLO 모델을 생성하여 추론
- **문제점** : API 요청마다 모델을 새롭게 로딩하면 모델 초기화에 불필요한 시간이 발생
- **원인** : 모델 객체의 생명주기를 관리하지 않고 요청 단위로 모델을 생성하는 구조이기 때문
- **해결방법** : `ModelManger`에서 모델 객체를 한 번만 생성하고 이후 요청에서는 기존 객체를 재사용하도록 구성

---

### 8. 객체 탐지 결과 이미지를 API 응답으로 반환
- **시도** : `/predict/visualize`에서 **YOLO**의 객체 탐지 결과에 **Bounding Box**를 표시한 이미지를 반환
- **문제점** : 일반적인 `/predict` API는 JSON을 반환하지만 `/predict/visualize`는 이미지 데이터를 반환해야 하므로 동일한 Response 방식을 사용할 수 없음
- **원인** : API의 목적에 따라 응답 데이터 형식이 다르기 때문
- **해결방법** : YOLO의 `result.plot()`을 이용하여 **Bounding Box**가 표시된 이미지를 생성한 후 **BytesIO**에 JPEG 형식으로 저장하고 **StreamingResponse**로 반환

---

### 8. FastAPI에서 DB 작업과 추론 로직의 책임 분리
- **시도** : `/predict` API에서 파일 업로드부터 YOLO 추론, 결과 파싱, DB 저장까지 한 번에 처리
- **문제점** : 하나의 Router 함수에 여러 책임이 집중되면 코드가 복잡해지고 각각의 기능을 독립적으로 수정하거나 테스트하기 어려움
- **원인** : API 요청을 처리하는 Router와 실제 비즈니스 로직이 분리되지 않았음
- **해결방법** : 기능별로 책임을 분리