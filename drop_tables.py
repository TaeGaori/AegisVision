from database import engine
from sqlalchemy import text

with engine.connect() as conn:
    conn.execute(text("DROP TABLE IF EXISTS detections"))
    conn.execute(text("DROP TABLE IF EXISTS detection_requests"))
    conn.commit()

print("테이블 삭제 완료")