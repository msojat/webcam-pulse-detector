import argparse
import json
import sys

import requests
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt, QRegExp
from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtWidgets import QWidget

from constants import constants
from lib.PulseApp import PulseApp


class Ui_Form(QWidget):
    def __init__(self, ok_button_callback, parent=None, Qt_WindowFlags_flags=Qt.Widget):
        super(Ui_Form, self).__init__(parent, Qt_WindowFlags_flags)

        self.setObjectName("Form")
        self.resize(485, 364)
        self.setStyleSheet("QWidget{ background-color: #ffffff; }")

        self.errorColor = '#f6989d'
        self.color = '#ffffff'

        ## Validation Flags ##
        self.isNameValid = False
        self.isSurnameValid = False
        self.isJmbagValid = False
        self.isRecordNumValid = True  # minimal default value is set
        self.isRecordLengthValid = True  # minimal default value is set

        # UI Creation and setup
        self.setupUi()

        # Connect ui parts (associate click listeners)
        self.ok_btn.clicked.connect(ok_button_callback)
        self.cancel_btn.clicked.connect(self.cancel_btn_click)

    def setupUi(self):
        ## Form elements (inputs) init ##
        self.name = QtWidgets.QLineEdit(self)
        self.name.setGeometry(QtCore.QRect(180, 50, 181, 21))
        self.name.setText("")
        self.name.setObjectName("name")
        self.name.setMaxLength(45)

        self.name_label = QtWidgets.QLabel(self)
        self.name_label.setGeometry(QtCore.QRect(110, 50, 60, 16))
        self.name_label.setObjectName("name_label")

        self.surname = QtWidgets.QLineEdit(self)
        self.surname.setGeometry(QtCore.QRect(180, 90, 181, 21))
        self.surname.setText("")
        self.surname.setObjectName("surname")
        self.surname.setMaxLength(45)

        self.surname_label = QtWidgets.QLabel(self)
        self.surname_label.setGeometry(QtCore.QRect(110, 90, 70, 16))
        self.surname_label.setObjectName("surname_label")

        self.jmbag = QtWidgets.QLineEdit(self)
        self.jmbag.setGeometry(QtCore.QRect(180, 130, 181, 21))
        self.jmbag.setText("")
        self.jmbag.setObjectName("jmbag")
        self.jmbag.setMaxLength(10)

        self.jmbag_label = QtWidgets.QLabel(self)
        self.jmbag_label.setGeometry(QtCore.QRect(110, 130, 60, 16))
        self.jmbag_label.setObjectName("jmbag_label")

        self.record_num = QtWidgets.QLineEdit(self)
        self.record_num.setGeometry(QtCore.QRect(260, 170, 101, 21))
        self.record_num.setText("5")
        self.record_num.setObjectName("record_num")
        self.record_num.setToolTip("Min 1, max 100")

        self.record_num_label = QtWidgets.QLabel(self)
        self.record_num_label.setGeometry(QtCore.QRect(110, 170, 131, 16))
        self.record_num_label.setObjectName("record_num_label")

        self.record_length = QtWidgets.QLineEdit(self)
        self.record_length.setGeometry(QtCore.QRect(260, 210, 101, 21))
        self.record_length.setText("30")
        self.record_length.setPlaceholderText("")
        self.record_length.setObjectName("record_length")
        self.record_length.setToolTip("Min 1, max 60")

        self.record_length_label = QtWidgets.QLabel(self)
        self.record_length_label.setGeometry(QtCore.QRect(110, 210, 111, 16))
        self.record_length_label.setObjectName("record_length_label")

        self.required = QtWidgets.QLabel(self)
        self.required.setGeometry(QtCore.QRect(110, 250, 111, 16))
        self.required.setObjectName("required")
        self.required.setText("Required *")
        self.required.setStyleSheet("#required { color: #c42033 }")

        self.ok_btn = QtWidgets.QPushButton(self)
        self.ok_btn.setGeometry(QtCore.QRect(250, 280, 113, 32))
        self.ok_btn.setObjectName("ok_btn")

        self.cancel_btn = QtWidgets.QPushButton(self)
        self.cancel_btn.setGeometry(QtCore.QRect(110, 280, 113, 32))
        self.cancel_btn.setObjectName("cancel_btn")

        self.retranslateUi(self)
        QtCore.QMetaObject.connectSlotsByName(self)

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

        self.setFixedSize(self.size())

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
                    # Response contains: identifier_id & user_id
                    self.data = json.loads(response.text)

                    self.data[u"record_length"] = int(self.record_length.text())
                    self.data[u"number_of_records"] = int(self.record_num.text())

            except Exception as err:
                error_msg = "Connection refused" if "Connection refused" in str(err.message) \
                    else str(err.message)

                self.showMessageBox(error_msg)

    def get_data(self):
        return self.data

    def cancel_btn_click(self):
        sys.exit()

    def showMessageBox(self, message):
        msg_box = QtWidgets.QMessageBox()
        msg_box.setText(message)
        msg_box.setIcon(QtWidgets.QMessageBox.Warning)
        msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg_box.exec_()

