import cv2
import threading

class CameraStream:
    def __init__(self):
        self.caps = {}
        self.running = False
        self.frames = {}
        self.threads = {}

    def start(self, sources):
        self.stop()  # Mevcut kameraları durdur

        for name, source in sources.items():
            cap = cv2.VideoCapture(source)
            if not cap.isOpened():
                print(f"Kamera {name} açılamadı!")
                continue

            self.caps[name] = cap
            self.frames[name] = None
            self.running = True
            self.threads[name] = threading.Thread(target=self.update, args=(name, cap))
            self.threads[name].start()

    def update(self, name, cap):
        while self.running and name in self.caps:
            ret, frame = cap.read()
            if not ret:
                print(f"Kare okunamadı: {name}")
                self.running = False
                break
            self.frames[name] = frame

    def read_frame(self, name):
        return self.frames.get(name)

    def stop(self):
        self.running = False
        for name, cap in self.caps.items():
            if name in self.threads:
                self.threads[name].join()
            cap.release()
        self.caps.clear()
        self.frames.clear()
        self.threads.clear()

    def add_camera(self, name, source):
        if name not in self.caps:
            cap = cv2.VideoCapture(source)
            if cap.isOpened():
                self.caps[name] = cap
                self.frames[name] = None
                self.running = True
                self.threads[name] = threading.Thread(target=self.update, args=(name, cap))
                self.threads[name].start()
            else:
                print(f"Kamera {name} açılamadı!")

    def remove_camera(self, name):
        if name in self.caps:
            cap = self.caps.pop(name)
            if name in self.threads:
                self.threads[name].join()
            cap.release()
            self.frames.pop(name, None)
            self.threads.pop(name, None)
            print(f"Kamera {name} kaldırıldı.")
