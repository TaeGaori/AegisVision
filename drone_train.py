from ultralytics import YOLO
import mlflow

mlflow.set_tracking_uri("sqlite:///mlflow.db")
mlflow.set_experiment("drone-detection")

# 사전학습된 가중치를 바로 불러옴
model = YOLO('runs/detect/train/weights/last.pt')

EPOCHS = 20
IMGSZ = 640
PATIENCE = 15


with mlflow.start_run():
    result = model.train(data="Drone_Data/data.yaml",
                        epochs = EPOCHS,
                        imgsz = IMGSZ,
                        patience = PATIENCE,
                        project="runs/detect",
                        name="train",
                        exist_ok=True
                        )
    
    metrics = model.val()

    mlflow.log_param('epochs', EPOCHS)
    mlflow.log_param('imgsz', IMGSZ)
    mlflow.log_metric('mAP50', metrics.box.map50)
    mlflow.log_metric("precision", metrics.box.mp)
    mlflow.log_metric("recall", metrics.box.mr)


