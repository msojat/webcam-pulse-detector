import argparse
import threading

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QLabel

from lib.PulseApp import PulseApp


class CameraLabel(QLabel):
    def __init__(self, parent=None):
        super(CameraLabel, self).__init__(parent=parent)

        # Setup pulse detector
        self.is_running = True
        self.thread_pulse_detector = None
        self.pulse_detector = self._create_pulse_detector()

    def _create_pulse_detector(self):
        parser = argparse.ArgumentParser(description='Webcam pulse detector.')
        parser.add_argument('--serial', default=None,
                            help='serial port destination for bpm data')
        parser.add_argument('--baud', default=None,
                            help='Baud rate for serial transmission')
        parser.add_argument('--udp', default=None,
                            help='udp address:port destination for bpm data')

        args = parser.parse_args()
        if not hasattr(self, "pulse_detector"):
            return PulseApp(args)
        else:
            return self.pulse_detector

    def open_camera(self, data):
        self.pulse_detector.setAppData(data)

        self.is_running = True
        self.thread_pulse_detector = threading.Thread(target=self.run_pulse_detector)
        self.thread_pulse_detector.start()

    def run_pulse_detector(self):
        print("Starting thread")
        while self.is_running:
            # Take camera image and process it
            self.pulse_detector.main_loop()

            # Get processed Image and show it in Label (self)
            ndarray_image = self.pulse_detector.processor.frame_out
            q_img = self.ndarray_to_qimage(ndarray_image)
            q_pixmap = QPixmap(q_img).scaledToHeight(150, Qt.SmoothTransformation)
            self.setPixmap(q_pixmap)

        print("Stopping thread")

    def ndarray_to_qimage(self, ndarray):
        height, width, channel = ndarray.shape
        bytes_per_line = 3 * width
        return QImage(ndarray.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()

    def cleanup(self):
        print("Cleaning up Camera Label")
        # Stop loop in Pulse Detector thread
        self.is_running = False
        if self.thread_pulse_detector is not None:
            # Wait for thread to join (stop)
            self.thread_pulse_detector.join()
            print("Waiting for thread to join")
        print("Thread joined...")
        # Cleanup Pulse Detector
        print("Closing Pulse App")
        self.pulse_detector.close()

        print("Cleaning done")
