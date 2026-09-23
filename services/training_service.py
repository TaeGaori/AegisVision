import mlflow
from mlflow.tracking import MlflowClient

MLFLOW_TRACKING_URI = "sqlite:///mlflow.db"
EXPERIMENT_NAME = "drone-detection"

# 요약용 run 이름 — 일반 세션 목록에서는 제외하고, 종합 결과로만 사용
CUMULATIVE_RUN_NAME = "cumulative_summary_v3"
CUMULATIVE_METRIC_KEYS = {
    "cumulative_mAP50": "mAP50",
    "cumulative_mAP50_95": "mAP50_95",
    "cumulative_precision": "precision",
    "cumulative_recall": "recall",
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

def _get_cumulative_metrics(client: MlflowClient, cumulative_run_id: str | None) -> dict:
    """cumulative_summary_v3 run에서 지표별 누적 곡선을 뽑아옴"""
    if cumulative_run_id is None:
        return {}

    result = {}
    for logged_name, display_key in CUMULATIVE_METRIC_KEYS.items():
        history = client.get_metric_history(cumulative_run_id, logged_name)
        history.sort(key=lambda x: x.step)
        if history:
            result[display_key] = [
                {"step": point.step, "value": point.value} for point in history
            ]
    return result

def get_training_history() -> dict:
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    client = MlflowClient()

    experiment = client.get_experiment_by_name(EXPERIMENT_NAME)
    if experiment is None:
        return {"total_sessions": 0, "total_epochs": 0, "runs": [], "cumulative_metrics": {}}

    runs = client.search_runs(
        experiment_ids=[experiment.experiment_id],
        order_by=["attributes.start_time ASC"]  
    )

    result_runs = []
    total_epochs = 0
    cumulative_run_id = None

    for run in runs:
        if run.info.run_name == CUMULATIVE_RUN_NAME:
            cumulative_run_id = run.info.run_id
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

    cumulative_metrics = _get_cumulative_metrics(client, cumulative_run_id)

    return{
        "total_sessions": len(result_runs),
        "total_epochs": total_epochs,
        "runs": result_runs,
        "cumulative_metrics": cumulative_metrics
    }
