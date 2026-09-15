from ultralytics import YOLO

model = YOLO('yolo26n.yaml')
model = YOLO('yolo26n.pt')
model = YOLO('yolo26n.yaml').load('yolo26n.pt')

result = model.train(data="coco8.yaml", epochs=100, imgsz=640)