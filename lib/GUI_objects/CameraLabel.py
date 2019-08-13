import argparse
import threading

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QLabel

from lib.PulseApp import PulseApp


class CameraLabel(QLabel):
    def __init__(self, parent=None):
        super(CameraLabel, self).__init__(parent=parent)

        # Setup pulse detector
        self.is_running = True
        self.thread_pulse_detector = None
        self.pulse_detector = None
        self.measurement_signal = None

        self.scale_image_down = False
        self.image_width_minimum = 400
        self.image_width_normal = 640

    def _create_pulse_detector(self):
        parser = argparse.ArgumentParser(description='Webcam pulse detector.')
        parser.add_argument('--serial', default=None,
                            help='serial port destination for bpm data')
        parser.add_argument('--baud', default=None,
                            help='Baud rate for serial transmission')
        parser.add_argument('--udp', default=None,
                            help='udp address:port destination for bpm data')

        args = parser.parse_args()
        if self.pulse_detector is None:
            pulse_detector = PulseApp(args)
            self.measurement_signal = pulse_detector.measurement_signal
            return pulse_detector
        else:
            return self.pulse_detector

    def open_camera(self, data):
        self.pulse_detector = self._create_pulse_detector()
        self.pulse_detector.setAppData(data)
        self.is_running = True
        self.thread_pulse_detector = threading.Thread(target=self.run_pulse_detector)
        self.thread_pulse_detector.start()

    def run_pulse_detector(self):
        while self.is_running:
            # Take camera image and process it
            self.pulse_detector.main_loop()

            # Get processed Image and show it in Label (self)
            ndarray_image = self.pulse_detector.processor.frame_out
            q_img = self.ndarray_to_qimage(ndarray_image)
            if self.scale_image_down:
                q_pixmap = QPixmap(q_img).scaledToWidth(self.image_width_minimum, Qt.SmoothTransformation)
            else:
                q_pixmap = QPixmap(q_img).scaledToWidth(self.image_width_normal, Qt.SmoothTransformation)
            self.setPixmap(q_pixmap)

    def ndarray_to_qimage(self, ndarray):
        height, width, channel = ndarray.shape
        bytes_per_line = 3 * width
        return QImage(ndarray.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()

    def set_scale_image_down_flag(self, value):
        self.scale_image_down = value

    def start_measuring(self):
        self.pulse_detector.start_measuring()

    def stop_measuring(self):
        self.pulse_detector.stop_measuring()

    def get_measurement(self):
        return self.pulse_detector.get_measurement()

    def cleanup(self):
        """
        Closes thread and closes pulse detector.

        !!! Has to be called !!!
        """
        # Stop loop in Pulse Detector thread
        self.is_running = False
        if self.thread_pulse_detector is not None and self.thread_pulse_detector.is_alive():
            # Wait for thread to join (stop)
            self.thread_pulse_detector.join()
        # Cleanup Pulse Detector
        if self.pulse_detector is not None:
            self.pulse_detector.close()
        print("Cleared Camera Label")
