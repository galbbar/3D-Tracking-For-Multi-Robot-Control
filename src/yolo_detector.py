import cv2
import numpy as np
from ultralytics import YOLO

class BallDetector:
    def __init__(self, model_path='../data/model/yolov8n.pt'):
        self.model = YOLO(model_path)

        # Calibración de cámaras
        left_calib = np.load("../data/calibration/left/left_calib.npy", allow_pickle=True).item()
        right_calib = np.load("../data/calibration/right/right_calib.npy", allow_pickle=True).item()
        stereo_calib = np.load("../data/calibration/stereo_calib.npy", allow_pickle=True).item()

        self.K1 = left_calib["camera_matrix"]
        self.K2 = right_calib["camera_matrix"]
        self.R = stereo_calib["R"]
        self.T = stereo_calib["T"]

        # Matrices de proyección
        self.P1 = self.K1 @ np.hstack((np.eye(3), np.zeros((3,1))))
        self.P2 = self.K2 @ np.hstack((self.R, self.T.reshape(3,1)))

    def detect_stereo_ball_position(self, left_path, right_path):
        centroides = []
        for image_path in [left_path, right_path]:
            image = cv2.imread(image_path)
            if image is None:
                return []
            results = self.model(image)

            for result in results:
                for box in result.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = box.conf[0].item()
                    cls_id = int(box.cls[0].item())
                    label = self.model.names[cls_id]

                    if label.lower() == "sports ball":
                        centroides.append(((x1 + x2) // 2, (y1 + y2) // 2))

        if len(centroides) == 2:
            point_4D = cv2.triangulatePoints(self.P1, self.P2, centroides[0], centroides[1])
            point_3D = point_4D[:3] / point_4D[3]
            puntos = [int(point_3D[i][0] * 100) if i != 2 else int(point_3D[i]) for i in range(3)]
            return puntos

        return []
