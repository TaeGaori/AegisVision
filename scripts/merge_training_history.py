import mlflow
from mlflow.tracking import MlflowClient

mlflow.set_tracking_uri("sqlite:///mlflow.db")
client = MlflowClient()

run_ids_in_order = [
    "bca3f4a18768457380c4ccc66903e1d7",  # unruly-shoat-509
    "b96e2d12e9264c6390ab4091d873bf19",  # useful-finch-355
    "e36ab1c31a524ca3941eda29d0712fbb",  # valuable-worm-661
    "67a47352630248dcbb39eb65e9ead3c6",  # adaptable-ray-497
]

# 뽑고 싶은 지표들 — (자동로깅 이름, 수동로깅 이름) 쌍으로 등록
metrics_to_merge = {
    "mAP50": ("metrics/mAP50B", "mAP50"),
    "mAP50_95": ("metrics/mAP50-95B", "mAP50-95"),
    "precision": ("metrics/precisionB", "precision"),
    "recall": ("metrics/recallB", "recall"),
}


def build_cumulative_series(metric_auto_name: str, metric_manual_name: str):
    all_steps = []
    all_values = []
    cumulative_offset = 0

    for run_id in run_ids_in_order:
        history = client.get_metric_history(run_id, metric_auto_name)
        if not history:
            history = client.get_metric_history(run_id, metric_manual_name)
        history.sort(key=lambda x: x.step)

        if not history:
            continue

        for point in history:
            all_steps.append(point.step + cumulative_offset)
            all_values.append(point.value)

        cumulative_offset += history[-1].step + 1

    return all_steps, all_values, cumulative_offset


mlflow.set_experiment("drone-detection")
with mlflow.start_run(run_name="cumulative_summary_v3"):
    final_total_epochs = 0

    for metric_key, (auto_name, manual_name) in metrics_to_merge.items():
        steps, values, total = build_cumulative_series(auto_name, manual_name)
        final_total_epochs = max(final_total_epochs, total)

        for step, value in zip(steps, values):
            mlflow.log_metric(f"cumulative_{metric_key}", value, step=step)

    mlflow.log_param("total_epochs", final_total_epochs)

print("완료! 4개 지표(mAP50, mAP50_95, precision, recall) 병합됨")