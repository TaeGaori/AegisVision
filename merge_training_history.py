
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

metrics_to_merge = {
    "mAP50": ("metrics/mAP50B", "mAP50"),
    "mAP50_95": ("metrics/mAP50-95B", "mAP50-95"),
    "precision": ("metrics/precisionB", "precision"),
    "recall": ("metrics/recallB", "recall"),
}


# 각 Run의 실제 완료 Epoch 계산
def get_actual_epochs(run_id: str) -> int:
    # train/box_loss를 기준으로 실제 완료 Epoch 계산
    history = client.get_metric_history(run_id, "train/box_loss")

    # 손실 기록이 없는 경우 mAP50 기록을 대체 기준으로 사용
    if not history:
        history = client.get_metric_history(run_id, "metrics/mAP50B")

    if not history:
        history = client.get_metric_history(run_id, "mAP50")

    if not history:
        return 0

    return max(point.step for point in history) + 1


# 여러 Run의 지표를 하나의 누적 시계열로 구성
def build_cumulative_series(
    metric_auto_name: str,
    metric_manual_name: str
):
    all_steps = []
    all_values = []

    # 누적 Epoch 위치
    cumulative_offset = 0

    for run_id in run_ids_in_order:
        # 자동 로깅 지표 조회
        metric_history = client.get_metric_history(
            run_id,
            metric_auto_name
        )

        # 자동 로깅 지표가 없으면 수동 로깅 지표 조회
        if not metric_history:
            metric_history = client.get_metric_history(
                run_id,
                metric_manual_name
            )

        # Epoch 순서대로 정렬
        metric_history.sort(key=lambda x: x.step)

        # 현재 Run의 지표를 누적 위치에 맞춰 이동
        for point in metric_history:
            all_steps.append(point.step + cumulative_offset)
            all_values.append(point.value)

        # 다음 Run의 시작 위치를 현재 Run의 실제 Epoch만큼 이동
        cumulative_offset += get_actual_epochs(run_id)

    # 모든 Run 처리가 끝난 후 반환
    return all_steps, all_values


# 전체 실제 완료 Epoch 합계
final_total_epochs = sum(
    get_actual_epochs(run_id)
    for run_id in run_ids_in_order
)


# Summary Run 생성
mlflow.set_experiment("drone-detection")

with mlflow.start_run(run_name="cumulative_summary_v3"):
    mlflow.set_tag("run_type", "cumulative_summary")

    for metric_key, (auto_name, manual_name) in metrics_to_merge.items():
        steps, values = build_cumulative_series(
            auto_name,
            manual_name
        )

        # 누적 지표 기록
        for step, value in zip(steps, values):
            mlflow.log_metric(
                f"cumulative_{metric_key}",
                value,
                step=step
            )

    # 실제 완료 Epoch 합계 기록
    mlflow.log_param("total_epochs", final_total_epochs)

print(f"완료! 4개 지표 병합됨")
print(f"총 실제 완료 Epoch: {final_total_epochs}")