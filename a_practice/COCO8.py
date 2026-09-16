from ultralytics import YOLO

"""
yolo train -> 처음

model = YOLO('yolo26n.yaml')
model = YOLO('yolo26n.pt')
model = YOLO('yolo26n.yaml').load('yolo26n.pt')

result = model.train(data="coco8.yaml", epochs=100, imgsz=640)
"""

"""
train에서 얻은 best.pt로 val()성능 평가

model = YOLO("runs/detect/train/weights/best.pt")  # 학습된 가중치 로드
metrics = model.val(data="coco8.yaml")
print(metrics)
"""

"""
내가 학습시킨 모델로 predict해보기

trained_model = YOLO("runs/detect/train/weights/best.pt")
results = trained_model("images.jpg")
results[0].show()
"""

"""
export()로 배포용 포맷 변환해보기

model = YOLO("runs/detect/train/weights/best.pt")
success = model.export(format="onnx")
print(success)
"""