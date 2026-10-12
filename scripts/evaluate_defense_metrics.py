# import json
# import time
# from pathlib import Path

# from ultralytics import YOLO

# MODEL_PATH = 'runs/detect/train_multiclass/weights/best.pt'
# DATA_YAML = 'multiclass_Data/data.yaml'
# OUTPUT_PATH = 'defense_metrics.json'

# # threshold를 스캔하면서 precision >= 0.95가 되는 지점을 찾음
# CONF_THRESHOLDS = [round(x, 2) for x in [i/100 for i in range(30, 100, 2)]]

# def find_recall_at_low_fpr(model: YOLO, target_precision: float = 0.95):
#     best_match = None

#     for conf in CONF_THRESHOLDS:
#         metrics = model.val(data=DATA_YAML, conf=conf, verbose=False)
#         precision = float(metrics.box.mp)
#         recall = float(metrics.box.mr)

#         # precision이 목표치 넘는 처음 지점
#         if precision >= target_precision:
#             best_match = {"conf_threshold": conf, "precision": precision, "recall": recall}
#             break

#     return best_match

# def benchmark_fps(model: YOLO, data_yaml: str, sample_size: int = 100):
#     """검증 이미지를 연속으로 추론시켜 처리 속도를 측정"""
#     import yaml
#     with open(data_yaml) as f:
#         data_cfg = yaml.safe_load(f)

#     val_dir = Path("multiclass_Data/valid/images")
#     jpg_paths = list(val_dir.glob("*.jpg"))
#     png_paths = list(val_dir.glob("*.png"))
#     image_paths = (jpg_paths + png_paths)[:sample_size]

#     if not image_paths:
#         return None

#     # 워밍업
#     model.predict(str(image_paths[0]), verbose=False)

#     start = time.time()
#     for path in image_paths:
#         model.predict(str(path), conf=0.5, verbose=False)
#     elapsed = time.time() - start

#     return {
#         "sample_size": len(image_paths),
#         "elapsed_sec": round(elapsed, 2),
#         "fps": round(len(image_paths) /elapsed, 2),
#     }

# if __name__ == "__main__":
#     model = YOLO(MODEL_PATH)

#     print("FPR=1%(precision>0.99) 지점의 recall 계산 중...")
#     low_fpr_result = find_recall_at_low_fpr(model)

#     print("FPS 벤치마크 측정 중...")
#     fps_result = benchmark_fps(model, DATA_YAML)

#     result = {
#         "low_fpr_recall": low_fpr_result,
#         "fps_benchmark": fps_result,
#         "model_path": MODEL_PATH
#     }

#     with open(OUTPUT_PATH, "w") as f:
#         json.dump(result, f, indent=2)

#     print(json.dumps(result, indent=2))
#     print(f"\n저장완료: {OUTPUT_PATH}")

"""
evaluate_defense_metrics.py (개선판)

측정하는 것
 1) 목표 precision(기본 0.95) 이상을 유지할 때의 Recall
    - "오탐을 일정 수준 이하로 억제했을 때 실제 드론을 얼마나 찾아내는가"
    - 객체 탐지에는 FPR 계산에 필요한 TN(정답 없음을 맞힌 수)이 없으므로
      FPR이라고 부르지 않고 precision 기준으로 정의한다.
 2) 추론 속도(FPS)
    - fps               : 이미지 읽기·전처리·후처리까지 포함한 전체 속도
    - inference_only_fps: 모델 추론 구간만의 속도

주의: Ultralytics 버전에 따라 곡선 속성 이름이 다를 수 있어,
      load_curves()에서 모양을 검사하고 이상하면 바로 에러를 내도록 했다.
"""
import json
import time
from pathlib import Path

import numpy as np
import torch
import ultralytics
from ultralytics import YOLO

# ── 설정 ──────────────────────────────────────────────────────────
MODEL_PATH = "runs/detect/train_multiclass/weights/best.pt"
DATA_YAML = "multiclass_Data/data.yaml"
VAL_IMAGES_DIR = Path("multiclass_Data/valid/images")  # FPS 측정에 쓸 검증 이미지 폴더
OUTPUT_PATH = "defense_metrics.json"

TARGET_PRECISION = 0.95          # 이 precision 이상이 되는 가장 낮은 신뢰도를 찾는다
FIXED_CONFS = [0.25, 0.50, 0.75]  # 해석하기 쉬운 고정 신뢰도 지점도 함께 기록
TARGET_CLASS = "drone"           # 안티드론 지표이므로 Drone 클래스만의 값도 따로 계산 (대소문자 무시)

FPS_SAMPLE_SIZE = 100
FPS_CONF = 0.5
WARMUP_RUNS = 5                  # 첫 호출들은 초기화 때문에 느려서 측정에서 제외


# ── 1. precision/recall 곡선 가져오기 ─────────────────────────────
def load_curves(model: YOLO):
    """검증을 '한 번만' 돌리고, 모든 신뢰도 지점의 precision/recall 곡선을 꺼낸다."""
    metrics = model.val(data=DATA_YAML, verbose=False)  # conf를 주지 않는다 (기본값으로 예측을 최대한 남김)
    box = metrics.box

    conf_axis = np.asarray(box.px)          # 신뢰도 0~1을 1000칸으로 나눈 축
    p_curve = np.asarray(box.p_curve)       # (클래스 수, 1000) 각 신뢰도에서의 precision
    r_curve = np.asarray(box.r_curve)       # (클래스 수, 1000) 각 신뢰도에서의 recall
    class_ids = [int(i) for i in box.ap_class_index]  # 곡선의 각 행이 어떤 클래스 번호인지
    names = {int(k): v for k, v in metrics.names.items()}

    if (p_curve.ndim != 2 or p_curve.shape[1] != conf_axis.shape[0]
            or p_curve.shape[0] != len(class_ids)):
        raise RuntimeError(
            f"예상과 다른 곡선 모양입니다: p_curve{p_curve.shape}, px{conf_axis.shape}, "
            f"classes={len(class_ids)}. Ultralytics 버전을 확인하세요."
        )
    return conf_axis, p_curve, r_curve, class_ids, names


# ── 2. 곡선에서 값 읽기 ───────────────────────────────────────────
def point_at_precision(conf_axis, p, r, target):
    """precision이 target 이상이 되는 '가장 낮은' 신뢰도 지점의 값을 반환한다.

    신뢰도가 낮을수록 recall이 높으므로, 목표 precision을 만족하는
    가장 낮은 신뢰도 = 목표 precision을 지키면서 recall이 가장 높은 지점이다.
    """
    hit = np.nonzero(p >= target)[0]
    if len(hit) == 0:
        return None  # 어떤 신뢰도에서도 목표 precision에 못 미침
    i = int(hit[0])
    return {
        "conf_threshold": round(float(conf_axis[i]), 3),
        "precision": round(float(p[i]), 4),
        "recall": round(float(r[i]), 4),
    }


def values_at(conf_axis, p, r, conf):
    """주어진 신뢰도에 가장 가까운 칸의 (precision, recall)."""
    i = int(np.argmin(np.abs(conf_axis - conf)))
    return float(p[i]), float(r[i])


def measure_recall_at_precision(model: YOLO):
    conf_axis, p_curve, r_curve, class_ids, names = load_curves(model)

    # 전체 클래스 평균 (기존 low_fpr_recall과 같은 의미의 값)
    p_mean, r_mean = p_curve.mean(axis=0), r_curve.mean(axis=0)

    # Drone 클래스만의 곡선 (행 번호 찾기)
    drone_row = next(
        (row for row, cid in enumerate(class_ids) if names.get(cid, "").lower() == TARGET_CLASS),
        None,
    )
    if drone_row is None:
        print(f"[경고] '{TARGET_CLASS}' 클래스를 찾지 못했습니다. names={names}")

    # 고정 신뢰도 지점
    fixed_points = []
    for conf in FIXED_CONFS:
        pm, rm = values_at(conf_axis, p_mean, r_mean, conf)
        item = {"conf_threshold": conf, "precision": round(pm, 4), "recall": round(rm, 4)}
        if drone_row is not None:
            pd, rd = values_at(conf_axis, p_curve[drone_row], r_curve[drone_row], conf)
            item["drone_precision"] = round(pd, 4)
            item["drone_recall"] = round(rd, 4)
        fixed_points.append(item)

    return {
        "target_precision": TARGET_PRECISION,
        "all_classes_mean": point_at_precision(conf_axis, p_mean, r_mean, TARGET_PRECISION),
        "drone_only": (
            point_at_precision(conf_axis, p_curve[drone_row], r_curve[drone_row], TARGET_PRECISION)
            if drone_row is not None else None
        ),
        "fixed_conf_points": fixed_points,
    }


# ── 3. FPS 측정 ───────────────────────────────────────────────────
def benchmark_fps(model: YOLO, sample_size: int = FPS_SAMPLE_SIZE):
    paths = sorted(
        p for ext in ("*.jpg", "*.jpeg", "*.png") for p in VAL_IMAGES_DIR.glob(ext)
    )[:sample_size]
    if not paths:
        print(f"[경고] 이미지가 없습니다: {VAL_IMAGES_DIR}")
        return None

    for p in paths[:WARMUP_RUNS]:  # 워밍업
        model.predict(str(p), conf=FPS_CONF, verbose=False)

    inference_ms = []
    start = time.perf_counter()
    for p in paths:
        result = model.predict(str(p), conf=FPS_CONF, verbose=False)
        inference_ms.append(result[0].speed["inference"])  # 모델 추론 구간(ms)
    elapsed = time.perf_counter() - start

    n = len(paths)
    mean_ms = float(np.mean(inference_ms))
    return {
        "sample_size": n,
        "elapsed_sec": round(elapsed, 2),
        "fps": round(n / elapsed, 2),                      # 기존 키 유지 (이미지 읽기 등 포함)
        "inference_only_fps": round(1000.0 / mean_ms, 2),  # 모델 추론만
        "mean_inference_ms": round(mean_ms, 2),
        "conf": FPS_CONF,
    }


def environment_info():
    return {
        "device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu",
        "ultralytics": ultralytics.__version__,
        "torch": torch.__version__,
    }


# ── 실행 ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    model = YOLO(MODEL_PATH)

    print(f"검증 세트로 곡선을 계산하는 중... (목표 precision {TARGET_PRECISION})")
    summary = measure_recall_at_precision(model)

    print("FPS 벤치마크 측정 중...")
    fps_result = benchmark_fps(model)

    result = {
        # 아래 두 키는 기존 API/대시보드가 읽는 이름이라 그대로 유지한다.
        "low_fpr_recall": summary["all_classes_mean"],
        "fps_benchmark": fps_result,
        "model_path": MODEL_PATH,
        # 아래는 새로 추가한 정보
        "recall_at_precision": summary,
        "environment": environment_info(),
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"\n저장 완료: {OUTPUT_PATH}")