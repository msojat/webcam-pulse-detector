import os
import sys
from random import randrange

from PyInstaller.compat import FileNotFoundError
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QColor
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel


class ImageWindow(QWidget):
    def __init__(self, relaxing_images_dir="images/relaxing", disturbing_images_dir="images/disturbing",
                 parent=None, Qt_WindowFlags_flags=Qt.Widget):
        super(ImageWindow, self).__init__(parent, Qt_WindowFlags_flags)

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

        ####
        # TODO: Check comments
        ####
        self.shown_images = []

    def show_relaxing_image(self):
        list_of_available_images = [image for image in self.relaxing_images if image not in self.shown_images]
        if len(list_of_available_images) < 1:
            raise FileNotFoundError("Not enough relaxing images in the folder")

        image = list_of_available_images[randrange(0, len(list_of_available_images))]
        pixmap = QPixmap('{0}/{1}'.format(self.relaxing_images_dir, image)).scaled(QSize(800, 700), Qt.KeepAspectRatio)
        self.findChild(QLabel, "image_label").setPixmap(pixmap)
        self.shown_images.append(image)

    def show_disturbing_image(self):
        list_of_available_images = [image for image in self.disturbing_images if image not in self.shown_images]
        if len(list_of_available_images) < 1:
            raise FileNotFoundError("Not enough disturbing images in the folder")

        image = list_of_available_images[randrange(0, len(list_of_available_images))]
        pixmap = QPixmap('{0}/{1}'
                         .format(self.disturbing_images_dir, image)).scaled(QSize(800, 700), Qt.KeepAspectRatio)
        self.findChild(QLabel, "image_label").setPixmap(pixmap)
        self.shown_images.append(image)

    def restart_shown_images(self):
        self.shown_images = []
