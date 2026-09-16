from ultralytics import YOLO
import mlflow

mlflow.set_experiment("drone-detection")

# 사전학습된 가중치를 바로 불러옴
model = YOLO('yolo26n.pt')

EPOCHS = 10
IMGSZ = 640
PATIENCE = 15


with mlflow.start_run():
    result = model.train(data="Drone_Data/data.yaml",
                        epochs = EPOCHS,
                        imgsz = IMGSZ,
                        patience = PATIENCE
                        )
    
    metrics = model.val()

    mlflow.log_param('epochs', EPOCHS)
    mlflow.log_param('imgsz', IMGSZ)
    mlflow.log_metric('mAP50', metrics.box.map50)
    mlflow.log_metric("precision", metrics.box.mp)
    mlflow.log_metric("recall", metrics.box.mr)


