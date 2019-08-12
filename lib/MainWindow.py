import argparse
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel

from lib.ImageWindow import ImageWindow
from lib.PulseApp import PulseApp
from lib.Ui_Form import Ui_Form


class MainWindow(QWidget):
    def __init__(self, parent=None, Qt_WindowFlags_flags=Qt.Widget):
        super(MainWindow, self).__init__(parent, Qt_WindowFlags_flags)

        # Widget for displaying starting form
        self.form_window = Ui_Form(self.form_ok_callback, self.form_cancel_callback, parent=self)
        self.image_window = ImageWindow(parent=self)

        layout = QHBoxLayout()
        layout.addWidget(self.form_window)
        self.setLayout(layout)

        self.pulse_detector = self._create_pulse_detector()

    def form_ok_cllback(self):
        if self.form_window:
            self.form_window.set_user()
            self.open_camera(self.form_window.get_data())
        else:
            sys.exit()
        # Change background color to teal
        p = self.palette()
        teal_color = QColor()
        teal_color.setRgb(0, 128, 128)
        p.setColor(self.backgroundRole(), teal_color)
        p.setColor(self.foregroundRole(), Qt.white)
        self.setPalette(p)

    def form_ok_callback(self):
        if self.form_window and self.form_window.check_state(None):
            if self.form_window.set_user():
                self.open_camera(self.form_window.get_data())

    def form_cancel_callback(self):
        self.close_program()

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

        self.layout().removeWidget(self.form_window)
        self.layout().addWidget(self.image_window)
        while True:
            self.pulse_detector.main_loop()

            ndarray_image = self.pulse_detector.processor.frame_out
            q_img = self.ndarray_to_qimage(ndarray_image)
            q_pixmap = QPixmap(q_img)
            self.image_window.findChild(QLabel, "image_label").setPixmap(q_pixmap)

    def ndarray_to_qimage(self, ndarray):
        height, width, channel = ndarray.shape
        bytes_per_line = 3 * width
        return QImage(ndarray.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()

    def close_program(self):
        print "Exiting"
        self.is_running = False
        if self.thread_pulse_detector is not None:
            self.thread_pulse_detector.join()
        self.pulse_detector.close()
        sys.exit()
