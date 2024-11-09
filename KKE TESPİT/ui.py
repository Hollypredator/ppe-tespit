import sys
import cv2
import threading
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QPushButton, QLineEdit, QMessageBox, QSplitter, QInputDialog, QMenu
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap
from camera_stream import CameraStream
from detection import DetectionModel
from screenshot_manager import ScreenshotManager

class CameraStream:
    def __init__(self):
        self.caps = {}
        self.running = False
        self.frames = {}
        self.threads = {}

    def start(self, sources):
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

    def remove_camera(self, name):
        if name in self.caps:
            self.caps[name].release()
            del self.caps[name]
        if name in self.frames:
            del self.frames[name]
        if name in self.threads:
            self.running = False
            self.threads[name].join()
            del self.threads[name]

    def add_camera(self, name, source):
        cap = cv2.VideoCapture(source)
        if not cap.isOpened():
            print(f"Kamera {name} açılamadı!")
            return
        
        self.caps[name] = cap
        self.frames[name] = None
        self.running = True
        self.threads[name] = threading.Thread(target=self.update, args=(name, cap))
        self.threads[name].start()

class CameraUI(QWidget):
    def __init__(self):
        super().__init__()

        # Kamera akışı, model ve ekran görüntüsü yöneticisi
        self.camera_stream = CameraStream()
        self.model = DetectionModel()
        self.screenshot_manager = ScreenshotManager()

        # Arayüzü başlat
        self.init_ui()

        # Zamanlayıcı
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)

    def init_ui(self):
        # Pencere başlığı ve boyutu
        self.setWindowTitle("Güvenlik Kamera İzleme ve PPE Tespit")
        self.setGeometry(100, 100, 1280, 720)  # Başlangıçta daha büyük pencere boyutu

        # Sol kısım: %30
        self.camera_list = QListWidget()
        self.camera_list.addItem("Ana Makine Kamerası (Yerleşik Kamera)")

        self.camera_input = QLineEdit()
        self.camera_input.setPlaceholderText("IP Kamera URL'si Girin")
        self.add_camera_button = QPushButton("Kamera Ekle")
        self.start_button = QPushButton("Program Başlat")
        self.stop_button = QPushButton("Program Durdur")
        self.open_folder_button = QPushButton("Klasörü Aç")

        # Sol kısım düzeni
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.camera_input)
        left_layout.addWidget(self.add_camera_button)
        left_layout.addWidget(self.camera_list)
        left_layout.addWidget(self.start_button)
        left_layout.addWidget(self.stop_button)
        left_layout.addWidget(self.open_folder_button)

        left_panel = QWidget()
        left_panel.setLayout(left_layout)

        # Sağ kısım: %70
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("background-color: #d3d3d3; border: 2px solid #000;")
        self.video_label.setScaledContents(False)  # Görüntüyü tam boyutlu göstermek için False

        right_layout = QVBoxLayout()
        right_layout.addWidget(self.video_label)

        right_panel = QWidget()
        right_panel.setLayout(right_layout)

        # QSplitter ile %30 - %70 oranını koruyalım
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([int(self.width() * 0.3), int(self.width() * 0.7)])  # Başlangıç oranları

        # Ana düzen
        main_layout = QHBoxLayout()
        main_layout.addWidget(splitter)

        self.setLayout(main_layout)

        # Buton işlevleri
        self.add_camera_button.clicked.connect(self.add_camera)
        self.start_button.clicked.connect(self.start_camera)
        self.stop_button.clicked.connect(self.stop_camera)
        self.open_folder_button.clicked.connect(self.screenshot_manager.open_screenshot_folder)

        # Sağ tıklama menüsü
        self.camera_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.camera_list.customContextMenuRequested.connect(self.show_context_menu)

    def show_context_menu(self, position):
        menu = QMenu()
        remove_action = menu.addAction("Sil")
        edit_action = menu.addAction("Düzenle")
        action = menu.exec_(self.camera_list.viewport().mapToGlobal(position))

        selected_camera = self.camera_list.currentItem()
        if selected_camera:
            camera_name = selected_camera.text()
            if action == remove_action:
                self.remove_camera(camera_name)
            elif action == edit_action:
                self.edit_camera(camera_name)

    def add_camera(self):
        url = self.camera_input.text()
        if url:
            name, ok = QInputDialog.getText(self, "Kamera Adı", "Kamera Adı:", QLineEdit.Normal)
            if ok and name:
                self.camera_list.addItem(name)
                self.camera_input.clear()
        else:
            QMessageBox.warning(self, "Uyarı", "Lütfen geçerli bir URL girin.")

    def start_camera(self):
        camera_items = self.camera_list.findItems("*", Qt.MatchWildcard)
        sources = {}
        for item in camera_items:
            name = item.text()
            if name == "Ana Makine Kamerası (Yerleşik Kamera)":
                sources[name] = 0
            else:
                sources[name] = self.camera_input.text()

        if not sources:
            QMessageBox.warning(self, "Uyarı", "Lütfen kameraları listeye ekleyin.")
            return

        self.camera_stream.start(sources)
        self.timer.start(30)  # 30 ms interval for updating frames

    def stop_camera(self):
        self.timer.stop()
        self.camera_stream.stop()
        self.video_label.clear()  # Kamera durdurulduğunda görüntüyü temizle

    def update_frame(self):
        selected_camera = self.camera_list.currentItem()
        if selected_camera is None:
            print("Kamera seçilmedi.")
            return

        camera_name = selected_camera.text()
        frame = self.camera_stream.read_frame(camera_name)

        if frame is None:
            print("Kare alınamadı.")
            return

        predictions = self.model.predict(frame)

        for pred in predictions['predictions']:
            x = int(pred['x'] - pred['width'] / 2)
            y = int(pred['y'] - pred['height'] / 2)
            w = int(pred['width'])
            h = int(pred['height'])

            label = pred['class']
            confidence = pred['confidence']

            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
            cv2.putText(frame, f'{label} ({confidence:.2f})', (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

            if label.lower() == 'no helmet':
                self.screenshot_manager.save_screenshot(frame)
                print("No Helmet tespit edildi, ekran görüntüsü alındı.")

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, channel = frame.shape
        step = channel * width
        q_img = QImage(frame.data, width, height, step, QImage.Format_RGB888)

        # QLabel boyutlarını güncelle
        self.video_label.setFixedSize(width, height)
        self.video_label.setPixmap(QPixmap.fromImage(q_img))

    def remove_camera(self, camera_name):
        self.camera_stream.remove_camera(camera_name)
        items = self.camera_list.findItems(camera_name, Qt.MatchExactly)
        if items:
            self.camera_list.takeItem(self.camera_list.row(items[0]))

    def edit_camera(self, camera_name):
        new_name, ok = QInputDialog.getText(self, "Yeni Kamera Adı", "Yeni Kamera Adı:", QLineEdit.Normal, camera_name)
        if ok and new_name:
            new_url, ok = QInputDialog.getText(self, "Yeni Kamera URL", "Yeni Kamera URL'si:", QLineEdit.Normal)
            if ok and new_url:
                self.camera_stream.remove_camera(camera_name)
                self.camera_stream.add_camera(new_name, new_url)
                items = self.camera_list.findItems(camera_name, Qt.MatchExactly)
                if items:
                    self.camera_list.item(self.camera_list.row(items[0])).setText(new_name)
                    self.camera_input.setText(new_url)

    def closeEvent(self, event):
        self.stop_camera()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CameraUI()
    window.show()
    sys.exit(app.exec_())
