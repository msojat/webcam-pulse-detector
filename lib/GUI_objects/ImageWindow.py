import os
import sys
import threading
import time
from random import randrange

from PyInstaller.compat import FileNotFoundError
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QPixmap, QColor
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QMessageBox


class ImageWindow(QWidget):
    MAX_SLEEP_DURATION = 2

    IMAGE_SET_ONE = 1
    IMAGE_SET_TWO = 2

    done_displaying_images_signal = pyqtSignal()
    display_image_signal = pyqtSignal(int)
    hide_image_signal = pyqtSignal()

    def __init__(self, config=None, parent=None, Qt_WindowFlags_flags=Qt.Widget):
        super(ImageWindow, self).__init__(parent, Qt_WindowFlags_flags)

        ###########
        # INIT UI #
        ###########
        # Define color palette
        # Change background color to teal
        p = self.palette()
        teal_color = QColor()
        teal_color.setRgb(0, 128, 128)
        p.setColor(self.backgroundRole(), teal_color)
        p.setColor(self.foregroundRole(), Qt.white)
        self.setPalette(p)

        # Create Image Label
        self.image_label = QLabel()
        self.image_label.setObjectName("image_label")

        # Put label in widget (self) using HBox Layout
        self.h_box = QHBoxLayout()
        self.h_box.addWidget(self.image_label)
        self.setLayout(self.h_box)

        #################################
        # Init Thread related variables #
        #################################
        self.thread_display_images = None
        self.is_running = True
        self.shown_images_counter = 0
        # Defined time (in seconds) for image display
        # and for pause between images
        self.image_timer = 30
        self.waiting_timer = 10
        self.image_showing_number = 10
        if config:
            if config['image_time']:
                self.image_timer = config['image_time']
            if config['pause_time']:
                self.waiting_timer = config['pause_time']
            if config['image_number']:
                self.image_showing_number = config['image_number']

        #######################################
        # Image Directories related variables #
        #######################################
        self.happiness_images_dir = "images/happiness"
        self.fear_images_dir = "images/fear"
        if config:
            if config['image_set_1_dir']:
                self.happiness_images_dir = config['image_set_1_dir']
            if config['image_set_2_dir']:
                self.fear_images_dir = config['image_set_2_dir']

        # Get image names and put them in lists
        try:
            self.relaxing_images = os.listdir(self.happiness_images_dir)
        except WindowsError:
            sys.exit("Relaxing folder ({0}) doesn't exist".format(self.happiness_images_dir))
        try:
            self.disturbing_images = os.listdir(self.fear_images_dir)
        except WindowsError:
            sys.exit("Disturbing folder ({0}) doesn't exist".format(self.fear_images_dir))

        self.shown_images = []
        self.current_showing_image = None

        self.msg_box = QMessageBox()

        self.display_image_signal.connect(self.show_image)
        self.hide_image_signal.connect(self.hide_image)

    def show_image(self, image_set):
        image_list = []
        images_dir = None
        error_text = "Not enough images in the image set"
        if image_set == self.IMAGE_SET_ONE:
            image_list = self.relaxing_images
            images_dir = self.happiness_images_dir
            error_text = "Not enough images in the image set 1 folder"
        if image_set == self.IMAGE_SET_TWO:
            image_list = self.disturbing_images
            images_dir = self.fear_images_dir
            error_text = "Not enough images in the image set 2 folder"

        list_of_available_images = [image_name for image_name in image_list
                                    if image_name not in self.shown_images]
        if len(list_of_available_images) < 1:
            self.is_running = False
            self.msg_box.setText(error_text)
            self.msg_box.exec_()
            self.close()

        image_name = list_of_available_images[randrange(0, len(list_of_available_images))]
        pixmap = QPixmap('{0}/{1}'.format(images_dir, image_name)).scaled(QSize(800, 700), Qt.KeepAspectRatio)
        self.image_label.setPixmap(pixmap)
        self.shown_images.append(image_name)
        self.current_showing_image = image_name

    def hide_image(self):
        self.image_label.clear()
        self.current_showing_image = None

    def _display_images(self):
        # While is_running flag is True, show and hide images
        while self.is_running:
            # Show 10 happiness then 10 fear images
            # Every image is shown for self.image_timer (default 30) seconds
            if self.shown_images_counter < self.image_showing_number:
                self.display_image_signal.emit(self.IMAGE_SET_ONE)
            else:
                self.display_image_signal.emit(self.IMAGE_SET_TWO)

            self.lazy_sleep(self.image_timer)

            # TODO: Remove `-1` and move increment before if
            if self.shown_images_counter == (2 * self.image_showing_number) - 1:
                self.shown_images_counter = 0
                self.is_running = False
                # send done_displaying_images signal
                self.done_displaying_images_signal.emit()
            self.shown_images_counter += 1

            # After the image is shown for specified duration,
            # clear it from the label and wait for self.WAITING_TIMER (default 10) seconds
            self.hide_image_signal.emit()
            self.lazy_sleep(self.waiting_timer)

    def lazy_sleep(self, sleep_time):
        """
        Function used to break sleep in segments of maximum 2s.
        Used to gracefully close application.
        """
        while sleep_time > self.MAX_SLEEP_DURATION:
            if not self.is_running:
                return
            time.sleep(self.MAX_SLEEP_DURATION)
            sleep_time = sleep_time - self.MAX_SLEEP_DURATION
        if not self.is_running:
            return
        time.sleep(sleep_time)

    def display_images(self):
        if self.thread_display_images is not None:
            self.stop_displaying_images()

        self.thread_display_images = threading.Thread(target=self._display_images)

        self.restart_shown_images()
        self.is_running = True
        if not self.thread_display_images.is_alive():
            self.thread_display_images.start()

    def stop_displaying_images(self):
        self.is_running = False
        if self.thread_display_images is not None and self.thread_display_images.is_alive():
            self.thread_display_images.join()
        self.thread_display_images = None
        self.restart_shown_images()

    def cleanup(self):
        self.is_running = False
        if self.thread_display_images is not None and self.thread_display_images.is_alive():
            self.thread_display_images.join()
        print("Cleared Image Window")

    def restart_shown_images(self):
        self.shown_images_counter = 0
        self.shown_images = []
        self.current_showing_image = None
