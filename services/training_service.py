import mlflow
from mlflow.tracking import MlflowClient

MLFLOW_TRACKING_URI = "sqlite:///mlflow.db"
EXPERIMENT_NAMES = ["drone-detection", "multiclass-detection"]

# 요약용 run 이름 — 일반 세션 목록에서는 제외하고, 종합 결과로만 사용
CUMULATIVE_RUN_NAME = "cumulative_summary_v3"
CUMULATIVE_METRIC_KEYS = {
    "mAP50": "metrics/mAP50B",
    "mAP50_95": "metrics/mAP50-95B",
    "precision": "metrics/precisionB",
    "recall": "metrics/recallB",
}


def _get_actual_completed_epochs(client:MlflowClient, run_id:str) -> int:
    """metric history의 마지막 step을 기준으로 실제 완료된 epoch 수를 구함"""
    history = client.get_metric_history(run_id, "train/box_loss")
    if not history:
        history = client.get_metric_history(run_id, "mAP50")
    if not history:
        return 0
    history.sort(key=lambda x:x.step)
    return history[-1].step + 1  # step은 0부터 시작하므로 +1

def  _build_cumulative_for_experiment(client: MlflowClient, experiment_name: str) -> dict:
    """특정 실험 하나의 run들을 시간순으로 이어붙여 지표별 누적 곡선을 만듦"""
    experiment = client.get_experiment_by_name(experiment_name)
    if experiment is None:
        return {}

    runs = client.search_runs(
        experiment_ids=[experiment.experiment_id],
        order_by=["attributes.start_time ASC"]
    )
    # 요약용 run은 원본이 아니라서 제외
    runs = [r for r in runs if not r.info.run_name.startswith("cumulative_summary")]

    result = {}
    for display_key, auto_logged_name in CUMULATIVE_METRIC_KEYS.items():
        all_steps = []
        all_values = []
        cumulative_offset = 0

        for run in runs:
            history = client.get_metric_history(run.info.run_id, auto_logged_name)
            if not history:
                # 자동 로깅 이름이 없으면 수동 로깅 이름으로 재시도
                manual_name = display_key.replace("_95", "-95")
                history = client.get_metric_history(run.info.run_id, manual_name)
            history.sort(key=lambda x: x.step)

            if not history:
                continue

            for point in history:
                all_steps.append(point.step + cumulative_offset)
                all_values.append(point.value)

            cumulative_offset += history[-1].step + 1

        if all_steps:
            result[display_key] = [
                {"step": step, "value": value} for step, value in zip(all_steps,all_values)
            ]

    return result

def get_training_history() -> dict:
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    client = MlflowClient()

    experiment_ids = []
    for name in EXPERIMENT_NAMES:
        experiment = client.get_experiment_by_name(name)
        if experiment is not None:
            experiment_ids.append(experiment.experiment_id)

    if not experiment_ids:
        return {
            "total_sessions": 0, 
            "total_epochs": 0, 
            "runs": [], 
            "cumulative_metrics": {"single_class": {}, "multi_class":{}}
            }

    runs = client.search_runs(
        experiment_ids=experiment_ids,
        order_by=["attributes.start_time ASC"]  
    )

    result_runs = []
    total_epochs = 0

    for run in runs:
        if run.info.run_name.startswith("cumulative_summary"):
            continue

        metrics = run.data.metrics
        params = run.data.params

        target_epochs_param = params.get("epochs")
        target_epochs = int(target_epochs_param) if target_epochs_param is not None else 0

        actual_epochs = _get_actual_completed_epochs(client, run.info.run_id)
        total_epochs += actual_epochs

        result_runs.append({
            "run_name": run.info.run_name,
            "run_id": run.info.run_id,
            "status": run.info.status,
            "epochs": target_epochs,    # 목표로 설정했던 값
            "actual_epochs": actual_epochs, # 실제로 완료된 값
            # 직접 기록, Ultralytics 자동 로깅된 지표 둘 다 커버
            "mAP50": metrics.get("metrics/mAP50B") or metrics.get("mAP50"),
            "mAP50_95": metrics.get("metrics/mAP50-95B") or metrics.get("mAP50_95"),
            "precision": metrics.get("metrics/precisionB") or metrics.get("precision"),
            "recall": metrics.get("metrics/recallB") or metrics.get("recall"),
            "started_at": str(run.info.start_time)
        })

    cumulative_metrics = {
        "single_class": _build_cumulative_for_experiment(client, "drone-detection"),
        "multi_class": _build_cumulative_for_experiment(client, "multiclass-detection"),
    }

    return{
        "total_sessions": len(result_runs),
        "total_epochs": total_epochs,
        "runs": result_runs,
        "cumulative_metrics": cumulative_metrics
    }
