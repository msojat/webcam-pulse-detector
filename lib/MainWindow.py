import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel

from lib.ImageWindow import ImageWindow
from lib.Ui_Form import Ui_Form


class MainWindow(QWidget):
    def __init__(self, parent=None, Qt_WindowFlags_flags=Qt.Widget):
        super(MainWindow, self).__init__(parent, Qt_WindowFlags_flags)

        self.form_window = Ui_Form(self.form_ok_cllback, parent=self)
        self.image_window = ImageWindow(parent=self)

        layout = QHBoxLayout()
        layout.addWidget(self.form_window)
        self.setLayout(layout)

    def form_ok_cllback(self):
        if self.form_window:
            self.form_window.set_user()
            self.form_window.open_camera(self.form_window.get_data(), self.image_window
                                         .findChild(QLabel, "image_label"))
        else:
            sys.exit()
