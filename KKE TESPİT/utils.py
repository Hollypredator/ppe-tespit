import os
from datetime import datetime

def create_screenshot_folder():
    if not os.path.exists('screenshots'):
        os.makedirs('screenshots')

def save_screenshot(camera_name, frame):
    create_screenshot_folder()
    timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
    filename = f"screenshots/{camera_name}_{timestamp}.png"
    cv2.imwrite(filename, frame)
    print(f"Screenshot saved as {filename}")
