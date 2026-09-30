# 학습 이어가기

from ultralytics import YOLO
import mlflow

def main():
    mlflow.set_tracking_uri("sqlite:///mlflow.db")
    mlflow.set_experiment("multiclass-detection")

    # 방금 학습이 끝난 가중치를 이어받음
    model = YOLO('runs/detect/train_multiclass/weights/last.pt')

    with mlflow.start_run():
        result = model.train(
            resume=True,
            epochs=100   # 목표 epoch를 늘림 (50 → 100)
        )

        metrics = model.val()

        mlflow.log_param('epochs', 100)
        mlflow.log_metric('mAP50', metrics.box.map50)
        mlflow.log_metric("precision", metrics.box.mp)
        mlflow.log_metric("recall", metrics.box.mr)


if __name__ == '__main__':
    main()