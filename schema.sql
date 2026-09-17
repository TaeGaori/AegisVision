-- schema.sql
-- AegisVision 드론 탐지 로그 저장용 스키마

-- 요청(이미지 업로드) 단위 테이블
CREATE TABLE IF NOT EXISTS detection_requests(
    "id"                SERIAL PRIMARY KEY,
    "filename"          VARCHAR(255) NOT NULL,
    "endpiont"          VARCHAR(50) NOT NULL,   -- 'predict' 또는 'predict_visualize'
    "requested_at"      TIMESTAMP NOT NULL DEFAULT NOW(),
    "model_path"        VARCHAR(255) NOT NULL, -- 예측한 가중치 파일이 뭔지
    "inference_time_ms" FLOAT,  -- 추론에 걸린 시간
    "detection_count"   INTEGER NOT NULL DEFAULT 0 -- 이 요청에서 탐지된 객체 수
)


-- 탐지된 객체 단위 테이블 (한 요청에 여러 행 가능)
CREATE TABLE IF NOT EXISTS detections (
    "id"              SERIAL PRIMARY KEY,
    "request_id"      INTEGER NOT NULL REFERENCES detection_requests(id) ON DELETE CASCADE,
    "class_name"      VARCHAR(50) NOT NULL,       -- 'drone'
    "confidence"      FLOAT NOT NULL,
    "bbox_x1"         FLOAT NOT NULL,
    "bbox_y1"         FLOAT NOT NULL,
    "bbox_x2"         FLOAT NOT NULL,
    "bbox_y2"         FLOAT NOT NULL
);


-- 조회 성능을 위한 인덱스
CREATE INDEX IF NOT EXISTS idx_detections_request_id ON detections(request_id);
CREATE INDEX IF NOT EXISTS idx_requests_requested_at ON detection_requests(requested_at);