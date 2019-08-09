from PyQt5.QtCore import QRegExp, QCoreApplication
from PyQt5.QtGui import QRegExpValidator

from lib.device import Camera
from lib.processors_noopenmdao import findFaceGetPulse
from lib.interface import plotXY, imshow, waitKey, destroyWindow
from cv2 import moveWindow
import argparse
import numpy as np
import datetime
from serial import Serial
import socket
import sys
import os
from os.path import expanduser
import platform
from PyQt5 import QtCore, QtGui, QtWidgets
import requests
import json
import time
from constants import constants
import inspect


def window():
    ########################
    #     UI Creation      #
    ########################
    app = QtWidgets.QApplication(sys.argv)

    form_window = QtWidgets.QWidget()
    Ui_Form().setupUi(form_window)
    form_window.setFixedSize(form_window.size())
    form_window.show()

    ################################################################
    # Configuration file creation / reading in HOME(~) directory   #
    ################################################################
    original_path = os.path.dirname(os.path.realpath(sys.argv[0]))

    # get $HOME folder
    path = expanduser("~")

    if platform.system() == constants.WINDOWS:
        constants.delimiter = "\\"
    else:
        constants.delimiter = "/"
    create_app_folder(path, constants.delimiter)

    with open(os.getcwd() + constants.delimiter + constants.CONFIG_JSON_FILE) as config:
        data = json.load(config)
        constants.BASE_URL = constants.get_host(data["http"], data["host"], data["port"])

    os.chdir(original_path)

    # Start GUI
    sys.exit(app.exec_())


def create_app_folder(path, delimiter):
    # create folder
    if not os.path.exists(path + delimiter + constants.FOLDER):
        os.makedirs(path + delimiter + constants.FOLDER)

    # go into folder
    os.chdir(path + delimiter + constants.FOLDER)
    # create file
    if not os.path.exists(constants.CONFIG_JSON_FILE):
        f = open(constants.CONFIG_JSON_FILE, 'w+')
        json_content = json.loads('{ "http": "http", "host": "localhost", "port": "3000" }')
        json.dump(json_content, f)
        f.close()


class getPulseApp(object):
    """
    Python application that finds a face in a webcam stream, then isolates the
    forehead.

    Then the average green-light intensity in the forehead region is gathered
    over time, and the detected person's pulse is estimated.
    """

    def __init__(self, args):
        # Imaging device - must be a connected camera (not an ip camera or mjpeg
        # stream)
        serial = args.serial
        baud = args.baud
        self.send_serial = False
        self.send_udp = False
        if serial:
            self.send_serial = True
            if not baud:
                baud = 9600
            else:
                baud = int(baud)
            self.serial = Serial(port=serial, baudrate=baud)

        udp = args.udp
        if udp:
            self.send_udp = True
            if ":" not in udp:
                ip = udp
                port = 5005
            else:
                ip, port = udp.split(":")
                port = int(port)
            self.udp = (ip, port)
            self.sock = socket.socket(socket.AF_INET,  # Internet
                                      socket.SOCK_DGRAM)  # UDP

        self.cameras = []
        self.selected_cam = 0
        for i in xrange(3):
            camera = Camera(camera=i)  # first camera by default
            if camera.valid or not len(self.cameras):
                self.cameras.append(camera)
            else:
                break
        self.w, self.h = 0, 0
        self.pressed = 0
        # Containerized analysis of recieved image frames (an openMDAO assembly)
        # is defined next.

        # This assembly is designed to handle all image & signal analysis,
        # such as face detection, forehead isolation, time series collection,
        # heart-beat detection, etc.

        # Basically, everything that isn't communication
        # to the camera device or part of the GUI
        self.processor = findFaceGetPulse(bpm_limits=[50, 160],
                                          data_spike_limit=2500.,
                                          face_detector_smoothness=10.)

        # Init parameters for the cardiac data plot
        self.bpm_plot = False
        self.plot_title = "Data display - raw signal (top) and PSD (bottom)"

        # Maps keystrokes to specified methods
        # (A GUI window must have focus for these to work)
        self.key_controls = {
            "s": self.toggle_search
        }

    def toggle_cam(self):
        if len(self.cameras) > 1:
            self.processor.find_faces = True
            self.bpm_plot = False
            destroyWindow(self.plot_title)
            self.selected_cam += 1
            self.selected_cam = self.selected_cam % len(self.cameras)

    def write_csv(self):
        """
        Writes current data to a csv file
        """
        fn = "Webcam-pulse" + str(datetime.datetime.now())
        fn = fn.replace(":", "_").replace(".", "_")
        data = np.vstack((self.processor.times, self.processor.samples)).T
        np.savetxt(fn + ".csv", data, delimiter=',')
        print "Writing csv"

    def toggle_search(self):
        """
        Toggles a motion lock on the processor's face detection component.

        Locking the forehead location in place significantly improves
        data quality, once a forehead has been sucessfully isolated.
        """
        # state = self.processor.find_faces.toggle()
        state = self.processor.find_faces_toggle(self.data)
        print "face detection lock =", not state

    def toggle_display_plot(self):
        """
        Toggles the data display.
        """
        if self.bpm_plot:
            print "bpm plot disabled"
            self.bpm_plot = False
            destroyWindow(self.plot_title)
        else:
            print "bpm plot enabled"
            if self.processor.find_faces:
                self.toggle_search()
            self.bpm_plot = True
            self.make_bpm_plot()
            moveWindow(self.plot_title, self.w, 0)

    def make_bpm_plot(self):
        """
        Creates and/or updates the data display
        """
        plotXY([[self.processor.times,
                 self.processor.samples],
                [self.processor.freqs,
                 self.processor.fft]],
               labels=[False, True],
               showmax=[False, "bpm"],
               label_ndigits=[0, 0],
               showmax_digits=[0, 1],
               skip=[3, 3],
               name=self.plot_title,
               bg=self.processor.slices[0])

    def key_handler(self):
        """
        Handle keystrokes, as set at the bottom of __init__.py()

        A plotting or camera frame window must have focus for keypresses to be
        detected.
        """

        self.pressed = waitKey(10) & 255  # wait for keypress for 10 ms
        if self.pressed == 27:  # exit program on 'esc'
            print "Exiting"
            for cam in self.cameras:
                cam.cam.release()
            if self.send_serial:
                self.serial.close()
            sys.exit()

        for key in self.key_controls.keys():
            if chr(self.pressed) == key:
                self.key_controls[key]()

    def main_loop(self):
        """
        Single iteration of the application's main loop.
        """
        # Get current image frame from the camera
        frame = self.cameras[self.selected_cam].get_frame()
        self.h, self.w, _c = frame.shape

        # display unaltered frame
        # imshow("Original",frame)

        # set current image frame to the processor's input
        self.processor.frame_in = frame
        # process the image frame to perform all needed analysis
        self.processor.run(self.selected_cam)
        # collect the output frame for display
        output_frame = self.processor.frame_out

        # show the processed/annotated output frame
        imshow("Processed", output_frame)

        # create and/or update the raw data display if needed
        if self.bpm_plot:
            self.make_bpm_plot()

        if self.send_serial:
            self.serial.write(str(self.processor.bpm) + "\r\n")

        if self.send_udp:
            self.sock.sendto(str(self.processor.bpm), self.udp)

        # handle any key presses
        self.key_handler()

    def setAppData(self, data):
        self.data = data
        self.processor.initData()


class Ui_Form(object):
    def setupUi(self, form_window):
        form_window.setObjectName("Form")
        form_window.resize(485, 364)
        form_window.setStyleSheet("QWidget{ background-color: #ffffff; }")

        self.form = form_window

        self.errorColor = '#f6989d'
        self.color = '#ffffff'

        ## Validation Flags ##
        self.isNameValid = False
        self.isSurnameValid = False
        self.isJmbagValid = False
        self.isRecordNumValid = True  # minimal default value is set
        self.isRecordLengthValid = True  # minimal default value is set

        ## Form elements (inputs) init ##
        self.name = QtWidgets.QLineEdit(form_window)
        self.name.setGeometry(QtCore.QRect(180, 50, 181, 21))
        self.name.setText("")
        self.name.setObjectName("name")
        self.name.setMaxLength(45)
        self.name_label = QtWidgets.QLabel(form_window)
        self.name_label.setGeometry(QtCore.QRect(110, 50, 60, 16))
        self.name_label.setObjectName("name_label")
        self.surname = QtWidgets.QLineEdit(form_window)
        self.surname.setGeometry(QtCore.QRect(180, 90, 181, 21))
        self.surname.setText("")
        self.surname.setObjectName("surname")
        self.surname.setMaxLength(45)
        self.surname_label = QtWidgets.QLabel(form_window)
        self.surname_label.setGeometry(QtCore.QRect(110, 90, 70, 16))
        self.surname_label.setObjectName("surname_label")
        self.jmbag = QtWidgets.QLineEdit(form_window)
        self.jmbag.setGeometry(QtCore.QRect(180, 130, 181, 21))
        self.jmbag.setText("")
        self.jmbag.setObjectName("jmbag")
        self.jmbag.setMaxLength(10)
        self.jmbag_label = QtWidgets.QLabel(form_window)
        self.jmbag_label.setGeometry(QtCore.QRect(110, 130, 60, 16))
        self.jmbag_label.setObjectName("jmbag_label")
        self.record_num = QtWidgets.QLineEdit(form_window)
        self.record_num.setGeometry(QtCore.QRect(260, 170, 101, 21))
        self.record_num.setText("5")
        self.record_num.setObjectName("record_num")
        self.record_num.setToolTip("Min 1, max 100")
        self.record_num_label = QtWidgets.QLabel(form_window)
        self.record_num_label.setGeometry(QtCore.QRect(110, 170, 131, 16))
        self.record_num_label.setObjectName("record_num_label")
        self.record_length = QtWidgets.QLineEdit(form_window)
        self.record_length.setGeometry(QtCore.QRect(260, 210, 101, 21))
        self.record_length.setText("30")
        self.record_length.setPlaceholderText("")
        self.record_length.setObjectName("record_length")
        self.record_length.setToolTip("Min 1, max 60")
        self.record_length_label = QtWidgets.QLabel(form_window)
        self.record_length_label.setGeometry(QtCore.QRect(110, 210, 111, 16))
        self.record_length_label.setObjectName("record_length_label")
        self.required = QtWidgets.QLabel(form_window)
        self.required.setGeometry(QtCore.QRect(110, 250, 111, 16))
        self.required.setObjectName("required")
        self.required.setText("Required *")
        self.required.setStyleSheet("#required { color: #c42033 }")
        self.ok_btn = QtWidgets.QPushButton(form_window)
        self.ok_btn.setGeometry(QtCore.QRect(250, 280, 113, 32))
        self.ok_btn.setObjectName("ok_btn")
        self.cancel_btn = QtWidgets.QPushButton(form_window)
        self.cancel_btn.setGeometry(QtCore.QRect(110, 280, 113, 32))
        self.cancel_btn.setObjectName("cancel_btn")

        self.retranslateUi(form_window)
        QtCore.QMetaObject.connectSlotsByName(form_window)

        # Connect ui parts (associate click listeners)
        self.ok_btn.clicked.connect(self.set_user)
        self.cancel_btn.clicked.connect(self.cancel_btn_click)

        # Set Input Validators
        numberValidator = QRegExpValidator(QRegExp("\d+"))
        self.jmbag.setValidator(numberValidator)
        self.record_num.setValidator(numberValidator)
        self.record_length.setValidator(numberValidator)

        nameValidator = QRegExpValidator(QRegExp("[a-zA-Z ]+"))
        self.name.setValidator(nameValidator)
        self.surname.setValidator(nameValidator)

        # Validate Input values on Text Change
        self.name.textChanged.connect(lambda: self.check_state(self.name))
        self.surname.textChanged.connect(lambda: self.check_state(self.surname))
        self.jmbag.textChanged.connect(lambda: self.check_state(self.jmbag))
        self.record_num.textChanged.connect(lambda: self.check_state(self.record_num))
        self.record_length.textChanged.connect(lambda: self.check_state(self.record_length))

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Login"))
        self.name_label.setText(_translate("Form", "Name *"))
        self.surname_label.setText(_translate("Form", "Surname *"))
        self.jmbag_label.setText(_translate("Form", "JMBAG *"))
        self.record_num_label.setText(_translate("Form", "Number of records *"))
        self.record_length_label.setText(_translate("Form", "Record length *"))
        self.ok_btn.setText(_translate("Form", "Ok"))
        self.cancel_btn.setText(_translate("Form", "Cancel"))

    def set_state(self, sender, color):
        sender.setStyleSheet('QLineEdit { background-color: %s }' % color)

    def check_state(self, sender):

        if sender == self.name:
            if len(self.name.text().strip()) > 0:
                self.isNameValid = True
                self.set_state(self.name, self.color)
            elif len(self.name.text().strip()) == 0:
                self.set_state(self.name, self.color)
                self.isNameValid = False
            else:
                self.set_state(self.name, self.errorColor)
                self.isNameValid = False

        if sender == self.surname:
            if len(self.surname.text().strip()) > 0:
                self.isSurnameValid = True
                self.set_state(self.surname, self.color)
            elif len(self.surname.text().strip()) == 0:
                self.set_state(self.surname, self.color)
                self.isSurnameValid = False
            else:
                self.set_state(self.surname, self.errorColor)
                self.isSurnameValid = False

        if sender == self.jmbag:
            if len(self.jmbag.text().strip()) == 10:
                self.isJmbagValid = True
                self.set_state(self.jmbag, self.color)
            elif len(self.jmbag.text().strip()) == 0:
                self.set_state(self.jmbag, self.color)
                self.isJmbagValid = False
            else:
                self.set_state(self.jmbag, self.errorColor)
                self.isJmbagValid = False

        if sender == self.record_num:
            if len(self.record_num.text()) > 0 and 1 <= int(self.record_num.text()) <= 100:
                self.isRecordNumValid = True
                self.set_state(self.record_num, self.color)
            elif len(self.record_num.text()) == 0:
                self.set_state(self.record_num, self.color)
                self.isRecordNumValid = False
            else:
                self.set_state(self.record_num, self.errorColor)
                self.isRecordNumValid = False

        if sender == self.record_length:
            if len(self.record_length.text()) > 0 and 1 <= int(self.record_length.text()) <= 60:
                self.isRecordLengthValid = True
                self.set_state(self.record_length, self.color)
            elif len(self.record_length.text()) == 0:
                self.set_state(self.record_length, self.color)
                self.isRecordLengthValid = False
            else:
                self.set_state(self.record_length, self.errorColor)
                self.isRecordLengthValid = False

        if self.isNameValid and self.isSurnameValid and self.isJmbagValid and self.isRecordNumValid \
                and self.isRecordLengthValid:
            return True
        else:
            return False

    def set_user(self):
        if self.check_state(None):
            url = "{0}{1}".format(constants.BASE_URL, "add_user")
            body = {
                "name": self.name.text().strip(),
                "surname": self.surname.text().strip(),
                "jmbag": self.jmbag.text(),
                "number_of_records": int(self.record_num.text()),
                "app_secret": constants.APP_SECRET
            }

            try:
                response = requests.post(url=url, data=body)

                if response.status_code == constants.STATUS_OK:
                    data = json.loads(response.text)

                    data[u"record_length"] = int(self.record_length.text())
                    data[u"number_of_records"] = int(self.record_num.text())

                    self.open_camera(data)

            except Exception as err:
                error_msg = "Connection refused" if str(err.message).__contains__("Connection refused") \
                    else str(err.message)

                self.showMessageBox(error_msg)

    def open_camera(self, data):
        parser = argparse.ArgumentParser(description='Webcam pulse detector.')
        parser.add_argument('--serial', default=None,
                            help='serial port destination for bpm data')
        parser.add_argument('--baud', default=None,
                            help='Baud rate for serial transmission')
        parser.add_argument('--udp', default=None,
                            help='udp address:port destination for bpm data')

        args = parser.parse_args()
        pulse_detector = getPulseApp(args)
        pulse_detector.setAppData(data)

        self.form.hide()

        while True:
            pulse_detector.main_loop()

    def cancel_btn_click(self):
        sys.exit()

    def showMessageBox(self, message):
        msg_box = QtWidgets.QMessageBox()
        msg_box.setText(message)
        msg_box.setIcon(QtWidgets.QMessageBox.Warning)
        msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg_box.exec_()


if __name__ == "__main__":
    window()
