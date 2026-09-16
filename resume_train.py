from ultralytics import YOLO
import mlflow

mlflow.set_experiment("drone-detection")

# resume=True는 last.pt에 저장된 설정(data, epochs, imgsz 등)을 그대로 이어받음
model = YOLO("runs/detect/train/weights/last.pt")

with mlflow.start_run():
    result = model.train(resume=True)   # 추가 trian -> epochs = '원하는 횟수'  

    metrics = model.val()

    mlflow.log_param("epochs", result.epoch)
    mlflow.log_metric("mAP50", metrics.box.map50)
    mlflow.log_metric("precision", metrics.box.mp)
    mlflow.log_metric("recall", metrics.box.mr)