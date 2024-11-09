import os
import cv2
from datetime import datetime
import subprocess

class ScreenshotManager:
    def __init__(self, save_directory="screenshots"):
        self.save_directory = save_directory
        if not os.path.exists(self.save_directory):
            os.makedirs(self.save_directory)

    def save_screenshot(self, frame):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(self.save_directory, f"screenshot_{timestamp}.png")
        cv2.imwrite(filepath, frame)
        print(f"Screenshot saved: {filepath}")

    def open_screenshot_folder(self):
        if os.name == 'nt':  # Windows
            os.startfile(self.save_directory)
        elif os.name == 'posix':  # macOS or Linux
            subprocess.Popen(['xdg-open', self.save_directory])
        else:
            print("Platform not supported for opening folder")
