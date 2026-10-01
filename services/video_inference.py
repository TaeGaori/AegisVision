import cv2
import tempfile
import os
import subprocess
from services.model_manager import model_manager

MAX_DURATION_SEC = 60   # 1분

def _reencode_to_h264(raw_path: str) -> str:
    """OpenCV가 쓴 영상을 브라우저 호환 H.264(libx264)로 재인코딩"""
    final_path = tempfile.mktemp(suffix=".mp4")
    try:
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", raw_path,
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                final_path,
            ],
            check=True,
            capture_output=True,
            timeout=120,
        )
    except subprocess.CalledProcessError as e:
        raise ValueError(f"비디오 재인코딩 실패: {e.stderr.decode(errors='ignore')[:300]}")
    finally:
        os.remove(raw_path)  # 원본(mp4v) 임시 파일은 정리

    return final_path


def process_video(input_path: str) -> tuple[str, dict]:
    model = model_manager.get_model()

    cap = cv2.VideoCapture(input_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)

    duration_sec = frame_count / fps if fps else 0
    if duration_sec > MAX_DURATION_SEC:
        cap.release()
        raise ValueError(f'비디오 길이는 {MAX_DURATION_SEC}초를 초과할 수 없습니다.')

    raw_path = tempfile.mktemp(suffix=".mp4")
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(raw_path, fourcc, fps, (width,height))

    if not writer.isOpened():
        cap.release()
        raise ValueError(f"비디오 writer를 열 수 없습니다 (코덱 문제일 수 있음): {raw_path}")

    total_frames = 0
    frames_with_detection = 0
    class_counts= {}

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        total_frames +=1

        results = model.predict(frame, conf=0.5, verbose=False)
        result = results[0]

        if len(result.boxes) > 0:
            frames_with_detection += 1
            for box in result.boxes:
                cls_name = result.names[int(box.cls)]
                class_counts[cls_name] = class_counts.get(cls_name, 0) +1

        plotted = result.plot()
        writer.write(plotted)

    cap.release()
    writer.release()

    output_path = _reencode_to_h264(raw_path)

    summary = {
        "total_frames": total_frames,
        "frames_with_detection": frames_with_detection,
        "class_counts": class_counts,
        "duration_sec": round(total_frames / fps, 1) if fps else None,
    }
    return output_path, summary