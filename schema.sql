-- schema.sql
-- AegisVision 드론 탐지 로그 저장용 스키마

-- 요청(이미지 업로드) 단위 테이블
CREATE TABLE IF NOT EXISTS detection_requests(
    "id"                SERIAL PRIMARY KEY,
    "filename"          VARCHAR(255) NOT NULL,
    "endpoint"          VARCHAR(50) NOT NULL,   -- 'predict' 또는 'predict_visualize'
    "requested_at"      TIMESTAMP NOT NULL DEFAULT NOW(),   -- API요청이 들어온 시간
    "model_path"        VARCHAR(255) NOT NULL, -- 예측한 가중치 파일이 뭔지
    "inference_time_ms" FLOAT,  -- 추론에 걸린 시간
    "detection_count"   INTEGER NOT NULL DEFAULT 0 -- 이 요청에서 탐지된 객체 수
)


-- 탐지된 객체 단위 테이블 (한 요청에 여러 행 가능)
CREATE TABLE IF NOT EXISTS detections (
    "id"              SERIAL PRIMARY KEY,
    -- ON DELETE CASCADE -> 부모가 삭제되면 자식도 삭제
    "request_id"      INTEGER NOT NULL REFERENCES detection_requests(id) ON DELETE CASCADE, -- 테이블 연결
    "class_name"      VARCHAR(50) NOT NULL,       -- YOLO가 탐지한 클래스 이름
    "confidence"      FLOAT NOT NULL,   -- YOLO의 confidence score
    "bbox_x1"         FLOAT NOT NULL,   -- 사각형 좌표
    "bbox_y1"         FLOAT NOT NULL,
    "bbox_x2"         FLOAT NOT NULL,
    "bbox_y2"         FLOAT NOT NULL
);


-- 조회 성능을 위한 인덱스
CREATE INDEX IF NOT EXISTS idx_detections_request_id ON detections(request_id);     -- request_id에 인덱스
CREATE INDEX IF NOT EXISTS idx_requests_requested_at ON detection_requests(requested_at); -- requested_at에 인덱스