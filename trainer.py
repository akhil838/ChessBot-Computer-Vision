import ultralytics
from ultralytics import settings

#settings["datasets_dir"] =  "/Users/akhil838/Documents/PyCharm_Projects/MiniProject"
model = ultralytics.models.YOLO('yolo11s')
model.train(data = 'Synthetic_Data/dataset.yaml',epochs = 5,device = 'cuda')
