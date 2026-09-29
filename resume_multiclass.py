# 학습 이어갈 때 쓰기

# resume_multiclass.py
import mlflow
from ultralytics import YOLO

mlflow.set_tracking_uri("sqlite:///mlflow.db")
mlflow.set_experiment("multiclass-detection")

model = YOLO('runs/detect/train_multiclass/weights/last.pt')

with mlflow.start_run():
    result = model.train(resume=True)   # data, epochs 등은 args.yaml에서 자동으로 읽어옴

    metrics = model.val()

    mlflow.log_param('epochs', 'resumed')  # 목표 epoch는 args.yaml에 이미 기록되어 있음
    mlflow.log_metric('mAP50', metrics.box.map50)
    mlflow.log_metric("precision", metrics.box.mp)
    mlflow.log_metric("recall", metrics.box.mr)