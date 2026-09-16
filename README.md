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
3. 학습 중 멈추면 (`resume_train.py`)로 재학습