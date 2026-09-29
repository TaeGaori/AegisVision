from ultralytics import YOLO
import mlflow

mlflow.set_tracking_uri("sqlite:///mlflow.db")
mlflow.set_experiment("multiclass-detection")

model = YOLO('yolo26n.pt')

EPOCHS = 40
IMGSZ = 640
PATIENCE = 15

result = model.train(data="multicalss_Data/data.yaml", epochs=2, imgsz=640, batch=16, device=0, name="gpu_test")

with mlflow.start_run():
    result = model.train(
        data="multiclass_Data/data.yaml",
        epochs=EPOCHS,
        imgsz= IMGSZ,
        patience=PATIENCE,
        batch=16,
        device=0,
        name="train_multiclass",
        exist_ok=True
    )

    metrics = model.val()

    mlflow.log_param('epochs', EPOCHS)
    mlflow.log_param('imgsz', IMGSZ)
    mlflow.log_metric('mAP50', metrics.box.map50)
    mlflow.log_metric("precision", metrics.box.mp)
    mlflow.log_metric("recall", metrics.box.mr)