import os
os.environ["MLFLOW_TRACKING_URI"] = "sqlite:///mlflow.db"
os.environ["MLFLOW_EXPERIMENT_NAME"] = "multiclass-detection"

from ultralytics import YOLO
import mlflow


def main():
    mlflow.set_tracking_uri("sqlite:///mlflow.db")
    mlflow.set_experiment("multiclass-detection")


    # uv run yolo settings mlflow=True 실행하고 학습시키기!!
    
    model = YOLO('yolo26n.pt')

    EPOCHS = 100
    IMGSZ = 640
    PATIENCE = 15

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

if __name__ == '__main__':
    main()

