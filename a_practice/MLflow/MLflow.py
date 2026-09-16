import mlflow

mlflow.set_experiment("test-experiment")

with mlflow.start_run():
    mlflow.log_param("epochs", 100)
    mlflow.log_param("imgsz", 640)
    mlflow.log_metric("mAP50", 0.89)
    mlflow.log_metric("precision", 0.76)