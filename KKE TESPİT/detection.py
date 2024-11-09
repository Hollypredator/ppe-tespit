# detection.py
import requests
import cv2
from config import ROBOFLOW_API_KEY, PROJECT_NAME, PROJECT_VERSION, CONFIDENCE_THRESHOLD, OVERLAP_THRESHOLD

class DetectionModel:
    def __init__(self):
        self.api_key = ROBOFLOW_API_KEY
        self.project_name = PROJECT_NAME
        self.project_version = PROJECT_VERSION
        self.confidence_threshold = CONFIDENCE_THRESHOLD
        self.overlap_threshold = OVERLAP_THRESHOLD
        self.model_url = f"https://detect.roboflow.com/{self.project_name}/{self.project_version}?api_key={self.api_key}&confidence={self.confidence_threshold}&overlap={self.overlap_threshold}"

    def predict(self, frame):
        _, img_encoded = cv2.imencode('.jpg', frame)
        response = requests.post(self.model_url, files={"file": img_encoded.tobytes()})
        return response.json() if response.status_code == 200 else {"predictions": []}
