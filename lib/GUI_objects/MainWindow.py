import sys
import time

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QMainWindow

from lib.GUI_objects.CameraLabel import CameraLabel
from lib.GUI_objects.ImageWindow import ImageWindow
from lib.GUI_objects.Ui_Form import Ui_Form
from lib.network.NetworkHelper import NetworkHelper


class MainWindow(QMainWindow):
    MEASUREMENTS_COUNT_LIMIT = 50

    def __init__(self, parent=None, window_flags=Qt.Widget):
        super(MainWindow, self).__init__(parent, window_flags)

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

        self.images = []
        self.bpm_array = []
        self.data = None
        self.session_id = None

    def form_ok_callback(self):
        if self.form_window and self.form_window.check_state(None):
            if self.form_window.set_user():
                ############
                # Read Data
                ############
                self.data = self.form_window.get_data()

                ############
                # Update UI
                ############
                self.main_widget.layout().removeWidget(self.form_window)
                self.form_window.hide()
                self.main_widget.layout().addWidget(self.camera_label)
                self.main_widget.layout().addWidget(self.image_widget)

                ###############
                # Start camera
                ###############
                self.camera_label.open_camera(self.data)

                ###########################
                # Connect signals to slots
                ###########################
                self.camera_label.measurement_signal.connect(self.measurement_slot)
                self.image_widget.done_displaying_images_signal.connect(self.stop_image_display)

    def measurement_slot(self):
        if self.image_widget.current_showing_image is not None and self.session_id is not None:
            single_measurement = {"value": self.camera_label.get_measurement(),
                                  "time": NetworkHelper.get_formatted_time(time.time()),
                                  "image": self.image_widget.current_showing_image}
            self.bpm_array.append(single_measurement)
            if len(self.bpm_array) == self.MEASUREMENTS_COUNT_LIMIT:
                self.send_measurements()

    def send_measurements(self):
        if self.data is None:
            return
        records = self.bpm_array[:self.MEASUREMENTS_COUNT_LIMIT]
        self.bpm_array = self.bpm_array[self.MEASUREMENTS_COUNT_LIMIT:]
        # get image if from database if not already fetched
        missing_images = list({bpm['image'] for bpm in records if bpm['image']
                               not in [image['name'] for image in self.images]})
        for img in missing_images:
            success, full_img = NetworkHelper.add_image({'name': img})
            if success:
                self.images.append(full_img)
        # change all records name with id
        for r in records:
            img_id = [img['id'] for img in self.images if r['image'] == img['name']]
            if not img_id:
                continue
            r['image'] = [img['id'] for img in self.images if r['image'] == img['name']][0]
        # send measurements (records)
        NetworkHelper.add_record_bulk(self.session_id, records)

    def form_cancel_callback(self):
        self.close_program()

    def closeEvent(self, event):
        """
        If program is closed by clicking on "X", perform cleanup before closing
        """
        self.camera_label.cleanup()
        self.image_widget.cleanup()
        event.accept()

    def keyPressEvent(self, e):
        """
        Handling key press
        """
        if e.key() == Qt.Key_Escape:
            self.close_program()

        if e.key() == Qt.Key_S:
            ##############################
            # Get new measurement session
            ##############################
            user_id = self.data[u"user_id"]
            is_success, self.session_id = NetworkHelper.create_measurement_session(user_id)
            if not is_success:
                print("New session request failed.")
                return

            #############################################
            # Start image displaying and pulse measuring
            #############################################
            # self.camera_label.pulse_detector.toggle_search()
            self.camera_label.start_measuring()
            # Start displaying images
            self.image_widget.display_images()
            self.camera_label.set_scale_image_down_flag(True)
            return

        if e.key() == Qt.Key_A:
            self.stop_image_display()
            return

        super(MainWindow, self).keyPressEvent(e)

    def stop_image_display(self):
        self.camera_label.stop_measuring()
        self.camera_label.set_scale_image_down_flag(False)
        self.image_widget.stop_displaying_images()
        self.send_measurements()

    def close_program(self):
        print("Exiting")
        self.camera_label.cleanup()
        self.image_widget.cleanup()
        sys.exit()
