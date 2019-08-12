import os
import sys
from random import randrange

from PyQt5.QtCore import Qt
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

        # Create Text label
        self.text_label = QLabel("Default text")
        self.text_label.setObjectName("text_label")

        self.text_h_box = QHBoxLayout()
        self.text_h_box.setObjectName("text_v_box")
        self.text_h_box.addStretch(1)
        self.text_h_box.addWidget(self.text_label)
        self.text_h_box.addStretch(1)

        # Create Image Label (holder)
        self.image_label = QLabel()
        self.image_label.setObjectName("image_label")

        #relaxing_images_list = os.listdir(self.relaxing_images_dir)
        #pixmap = QPixmap('{0}/{1}'.format(self.relaxing_images_dir, relaxing_images_list
        #    [randrange(0, len(relaxing_images_list))]))
        #self.image_label.setPixmap(pixmap)

        self.v_box = QVBoxLayout()
        self.v_box.addLayout(self.text_h_box)
        self.v_box.addWidget(self.image_label)

        self.h_box = QHBoxLayout()
        self.h_box.addStretch(1)
        self.h_box.addLayout(self.v_box)
        self.h_box.addStretch(1)

        self.setLayout(self.h_box)

        ####
        #
        ####
        self.shown_images = []

    def show_relaxing_image(self):
        list_of_availabe_images = [image for image in self.relaxing_images if image not in self.shown_images]
        if len(list_of_availabe_images) < 1:
            sys.exit("Not enough relaxing images in the folder")

        image = list_of_availabe_images[randrange(0, len(list_of_availabe_images))]
        pixmap = QPixmap('{0}/{1}'.format(self.relaxing_images_dir, image))
        self.findChild(QLabel, "image_label").setPixmap(pixmap)

        self.shown_images.append(image)
