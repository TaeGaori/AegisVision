import cv2
import tempfile
import os
from services.model_manager import model_manager

MAX_DURATION_SEC = 60   # 1분

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

    output_path = tempfile.mktemp(suffix=".mp4")
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(output_path, fourcc, fps, (width,height))

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

    summary = {
        "total_frames": total_frames,
        "frames_with_detection": frames_with_detection,
        "class_counts": class_counts,
        "duration_sec": round(total_frames / fps, 1) if fps else None,
    }
    return output_path, summary