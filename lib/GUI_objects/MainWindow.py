import sys
import time

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QMainWindow

from lib.GUI_objects.CameraLabel import CameraLabel
from lib.GUI_objects.ImageWindow import ImageWindow
from lib.GUI_objects.Ui_Form import Ui_Form


class MainWindow(QMainWindow):
    def __init__(self, parent=None, Qt_WindowFlags_flags=Qt.Widget):
        super(MainWindow, self).__init__(parent, Qt_WindowFlags_flags)

        # Create main widget for MainWindow
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)

        # Widget for displaying starting form
        self.form_window = Ui_Form(self.form_ok_callback, self.form_cancel_callback)
        # Widget for displaying camera image
        self.camera_label = CameraLabel()
        # Widget for displaying images
        self.image_widget = ImageWindow()

        layout = QHBoxLayout()
        layout.addWidget(self.form_window)
        self.main_widget.setLayout(layout)

        # Change background color to teal
        # and text to white
        p = self.palette()
        teal_color = QColor()
        teal_color.setRgb(0, 128, 128)
        p.setColor(self.backgroundRole(), teal_color)
        p.setColor(self.foregroundRole(), Qt.white)
        self.setPalette(p)

        self.bpm_array = []

    def form_ok_callback(self):
        if self.form_window and self.form_window.check_state(None):
            if self.form_window.set_user():
                # self.open_camera(self.form_window.get_data())

                self.main_widget.layout().removeWidget(self.form_window)
                self.form_window.hide()
                self.main_widget.layout().addWidget(self.camera_label)
                self.main_widget.layout().addWidget(self.image_widget)

                self.image_widget.show_relaxing_image()

                self.camera_label.open_camera(self.form_window.get_data())
                self.camera_label.measurement_signal.connect(self.measurement_slot)

    def measurement_slot(self):
        # TODO: Add Measurement, time and image name/id to list
        #  Send measurements data to server
        if self.image_widget.current_showing_image is not None:
            single_measurement = {"value": self.camera_label.get_measurement(),
                                  "time": time.time(),
                                  "image": self.image_widget.current_showing_image}
            print(single_measurement)

    def form_cancel_callback(self):
        self.close_program()

    def keyPressEvent(self, e):
        """
        Handling key press
        """
        if e.key() == Qt.Key_Escape:
            self.close_program()

        if e.key() == Qt.Key_S:
            # self.camera_label.pulse_detector.toggle_search()
            self.camera_label.start_measuring()
            # Start displaying images
            self.image_widget.display_images()
            return

        if e.key() == Qt.Key_A:
            self.camera_label.stop_measuring()
            return

        super(MainWindow, self).keyPressEvent(e)

    def close_program(self):
        print("Exiting")
        self.camera_label.cleanup()
        self.image_widget.cleanup()
        sys.exit()
