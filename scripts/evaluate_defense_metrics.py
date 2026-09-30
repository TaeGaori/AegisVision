import json
import time
from pathlib import Path

from ultralytics import YOLO

MODEL_PATH = 'runs/detect/train_multiclass/weights/best.pt'
DATA_YAML = 'multiclass_Data/data.yaml'
OUTPUT_PATH = 'defense_metrics.json'

# threshold를 스캔하면서 precision >= 0.99가 되는 지점을 찾음
CONF_THRESHOLDS = [round(x, 2) for x in [i/100 for i in range(30, 100, 2)]]

def find_recall_at_low_fpr(model: YOLO, target_presision: float = 0.99):
    best_match = None

    for conf in CONF_THRESHOLDS:
        metrics = model.val(data=DATA_YAML, conf=conf, verbose=False)
        precision = float(metrics.box.mp)
        recall = float(metrics.box.mr)

        # precision이 목표치 넘는 처음 지점
        if precision >= target_presision:
            best_match = {"conf_threshold": conf, "precision": precision, "recall": recall}
            break

        return best_match

def benchmark_fps(model: YOLO, data_yaml: str, sample_size: int = 100):
    """검증 이미지를 연속으로 추론시켜 처리 속도를 측정"""
    import yaml
    with open(data_yaml) as f:
        data_cfg = yaml.safe_load(f)

    val_dir = Path(data_yaml).parent / data_cfg["val"]
    image_paths = list(val_dir.glob("*.jpg")[:sample_size] + list(val_dir.glob("*.png"))[:sample_size])
    image_paths = image_paths[:sample_size]

    if not image_paths:
        return None

    # 워밍업
    model.predict(str(image_paths[0]), verbose=False)

    start = time.time()
    for path in image_paths:
        model.predict(str(path), conf=0.5, verbose=False)
    elapsed = time.time() - start

    return {
        "sample_size": len(image_paths),
        "elapsed_sec": round(elapsed, 2),
        "fps": round(len(image_paths) /elapsed, 2),
    }

if __name__ == "__main__":
    model = YOLO(MODEL_PATH)

    print("FPR=1%(precision>0.99) 지점의 recall 계산 중...")
    low_fpr_result = find_recall_at_low_fpr(model)

    print("FPS 벤치마크 측정 중...")
    fps_result = benchmark_fps(model, DATA_YAML)

    result = {
        "low_fpr_recall": low_fpr_result,
        "fps_benchmark": fps_result,
        "model_path": MODEL_PATH
    }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(result, f, indent=2)

    print(json.dumps(result, indent=2))
    print(f"\n저장완료: {OUTPUT_PATH}")