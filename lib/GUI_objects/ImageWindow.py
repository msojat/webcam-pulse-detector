import os
import sys
import threading
import time
from random import randrange

from PyInstaller.compat import FileNotFoundError
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QColor
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel


class ImageWindow(QWidget):
    def __init__(self, relaxing_images_dir="images/relaxing", disturbing_images_dir="images/disturbing",
                 parent=None, Qt_WindowFlags_flags=Qt.Widget):
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

        # Create Image Label (holder)
        self.image_label = QLabel()
        self.image_label.setObjectName("image_label")

        self.h_box = QHBoxLayout()
        self.h_box.addWidget(self.image_label)

        self.setLayout(self.h_box)

        #################################
        # Init Thread related variables #
        #################################
        self.thread_display_images = threading.Thread(target=self._display_images)
        self.is_running = True
        self.shown_images_counter = 0
        # Defined time (in seconds) for image display
        # and for pause between images
        self.IMAGE_TIMER = 30
        self.WAITING_TIMER = 10

        #######################################
        # Image Directories related variables #
        #######################################
        self.relaxing_images_dir = relaxing_images_dir
        self.disturbing_images_dir = disturbing_images_dir

        # Get image names and put them in lists
        try:
            self.relaxing_images = os.listdir(relaxing_images_dir)
        except WindowsError:
            sys.exit("Relaxing folder ({0}) doesn't exist".format(relaxing_images_dir))
        try:
            self.disturbing_images = os.listdir(disturbing_images_dir)
        except WindowsError:
            sys.exit("Disturbing folder ({0}) doesn't exist".format(disturbing_images_dir))

        self.shown_images = []
        self.current_showing_image = None

    def show_relaxing_image(self):
        list_of_available_images = [image_name for image_name in self.relaxing_images if image_name not in self.shown_images]
        if len(list_of_available_images) < 1:
            raise FileNotFoundError("Not enough relaxing images in the folder")

        image_name = list_of_available_images[randrange(0, len(list_of_available_images))]
        pixmap = QPixmap('{0}/{1}'.format(self.relaxing_images_dir, image_name)).scaled(QSize(800, 700), Qt.KeepAspectRatio)
        self.findChild(QLabel, "image_label").setPixmap(pixmap)
        self.shown_images.append(image_name)
        self.current_showing_image = image_name

    def show_disturbing_image(self):
        list_of_available_images = [image_name for image_name in self.disturbing_images if image_name not in self.shown_images]
        if len(list_of_available_images) < 1:
            raise FileNotFoundError("Not enough disturbing images in the folder")

        image_name = list_of_available_images[randrange(0, len(list_of_available_images))]
        pixmap = QPixmap('{0}/{1}'
                         .format(self.disturbing_images_dir, image_name)).scaled(QSize(800, 700), Qt.KeepAspectRatio)
        self.findChild(QLabel, "image_label").setPixmap(pixmap)
        self.shown_images.append(image_name)
        self.current_showing_image = image_name

    def _display_images(self):
        # While is_running flag is True, show and hide images
        while self.is_running:
            # Show 10 relaxing then 10 disturbing images
            # Every image is shown for self.IMAGE_TIMER (default 30) seconds
            if self.shown_images_counter < 10:
                self.show_relaxing_image()
            else:
                self.show_disturbing_image()

            if self.shown_images_counter == 19:
                self.shown_images_counter = 0
                self.is_running = False
            self.shown_images_counter += 1
            self.lazy_sleep(self.IMAGE_TIMER)

            # After the image is shown for specified duration,
            # clear it from the label and wait for self.WAITING_TIMER (default 10) seconds
            self.findChild(QLabel, "image_label").clear()
            self.current_showing_image = None

            self.lazy_sleep(self.WAITING_TIMER)

    def lazy_sleep(self, sleep_time):
        """
        Function used to break sleep in segments of maximum 2s.
        Used to gracefully close application.
        """
        MAX_SLEEP_DURATION = 2
        while sleep_time > MAX_SLEEP_DURATION:
            if not self.is_running:
                return
            time.sleep(MAX_SLEEP_DURATION)
            sleep_time = sleep_time - MAX_SLEEP_DURATION
        if not self.is_running:
            return
        time.sleep(sleep_time)

    def display_images(self):
        if not self.thread_display_images.is_alive():
            self.restart_shown_images()

            self.is_running = True
            self.thread_display_images.start()

    def cleanup(self):
        self.is_running = False
        if self.thread_display_images.is_alive():
            self.thread_display_images.join()
        print("Cleared Image Window")

    def restart_shown_images(self):
        self.shown_images_counter = 0
        self.shown_images = []
