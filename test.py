import torch
import numpy as np
import cv2
from time import time
from ultralytics import YOLO
import supervision as sv


class ObjectDetection:

    def __init__(self, capture_index):
        self.capture_index = capture_index
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print("Using Device:", self.device)
        self.model = self.load_model()
        self.CLASS_NAMES_DICT = self.model.model.names
        self.box_annotator = sv.BoxAnnotator(sv.ColorPalette.default(), thickness=3, text_thickness=3, text_scale=1.5)
    

    def load_model(self):
        model = YOLO("yolov8x.pt")  # load a pretrained YOLOv8n model
        model.fuse()
        return model


    def predict(self, frame):
        results = self.model(frame)
        return results
    

    def plot_bboxes(self, results, frame):
        try:
            if len(results) == 0:
                return frame
            
            xyxys = []
            confidences = []
            class_ids = []
            
            # Extract detections for person class
            for result in results:
                boxes = result.boxes.cpu().numpy()
                class_id = boxes.cls[0]
                conf = boxes.conf[0]
                xyxy = boxes.xyxy[0]
        
                if class_id == 0.0:
                    xyxys.append(result.boxes.xyxy.cpu().numpy())
                    confidences.append(result.boxes.conf.cpu().numpy())
                    class_ids.append(result.boxes.cls.cpu().numpy().astype(int))
            
            if len(xyxys) == 0:
                return frame
                
            # Setup detections for visualization
            detections = sv.Detections(
                xyxy=xyxys[0],
                confidence=confidences[0],
                class_id=class_ids[0],
            )
        
            # Format custom labels
            self.labels = [f"{self.CLASS_NAMES_DICT[class_id]} {confidence:0.2f}" for confidence, class_id in zip(detections.confidence, detections.class_id)]
            
            # Annotate and display frame
            frame = self.box_annotator.annotate(scene=frame, detections=detections, labels=self.labels)
        except IndexError:
            pass
        
        return frame
    
    
    def __call__(self):
        cap = cv2.VideoCapture(self.capture_index)
        assert cap.isOpened()
        print("Hi")
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
      
        while True:
            start_time = time()
            
            ret, frame = cap.read()
            assert ret
            
            results = self.predict(frame)
            frame = self.plot_bboxes(results, frame)
            
            end_time = time()
            fps = 1/np.round(end_time - start_time, 2)
            cv2.putText(frame, f'FPS: {int(fps)}', (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 2)
            
            cv2.imshow('YOLOv8 Detection', frame)
 
            if cv2.waitKey(5) & 0xFF == 27:
                break
        
        cap.release()
        cv2.destroyAllWindows()


detector = ObjectDetection(capture_index=0)
detector()