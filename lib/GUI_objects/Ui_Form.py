from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt, QRegExp
from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtWidgets import QWidget, QFormLayout, QHBoxLayout, QVBoxLayout

from lib.network.NetworkHelper import NetworkHelper


class Ui_Form(QWidget):
    def __init__(self, ok_button_callback, cancel_button_callback, parent=None, Qt_WindowFlags_flags=Qt.Widget):
        super(Ui_Form, self).__init__(parent, Qt_WindowFlags_flags)

        self.setObjectName("Form")
        self.resize(485, 364)

        self.errorColor = '#f6989d'
        self.color = '#ffffff'

        # Validation Flags ##
        self.isNameValid = False
        self.isSurnameValid = False
        self.isJmbagValid = False
        self.isRecordNumValid = True  # minimal default value is set
        self.isRecordLengthValid = True  # minimal default value is set

        # Flag used for session name field auto generation ##
        self.session_text_edited_flag = False

        # UI Creation and setup
        self.setupUi()

        # Connect ui parts (associate click listeners)
        self.ok_btn.clicked.connect(ok_button_callback)
        self.cancel_btn.clicked.connect(cancel_button_callback)

    def setupUi(self):
        ## Form elements (inputs) init ##
        self.name = QtWidgets.QLineEdit()
        self.name.setText("")
        self.name.setObjectName("name")
        self.name.setMaxLength(45)
        self.name.textEdited.connect(self.update_session_name)

        self.surname = QtWidgets.QLineEdit()
        self.surname.setText("")
        self.surname.setObjectName("surname")
        self.surname.setMaxLength(45)
        self.surname.textEdited.connect(self.update_session_name)

        self.jmbag = QtWidgets.QLineEdit()
        self.jmbag.setText("")
        self.jmbag.setObjectName("jmbag")
        self.jmbag.setMaxLength(10)

        self.record_num = QtWidgets.QLineEdit()
        self.record_num.setText("5")
        self.record_num.setObjectName("record_num")
        self.record_num.setToolTip("Min 1, max 100")

        self.record_length = QtWidgets.QLineEdit()
        self.record_length.setText("30")
        self.record_length.setPlaceholderText("")
        self.record_length.setObjectName("record_length")
        self.record_length.setToolTip("Min 1, max 60")

        self.session_name = QtWidgets.QLineEdit()
        self.session_name.setText("")
        self.session_name.setObjectName("name")
        self.session_name.setMaxLength(45)
        self.session_name.textEdited.connect(self.session_text_edited)

        self.required = QtWidgets.QLabel()
        self.required.setObjectName("required")
        self.required.setText("Required *")
        self.required.setStyleSheet("#required { color: #c42033 }")

        # Create Form Layout and put all form elements in it
        self.form_layout = QFormLayout()
        self.form_layout.addRow("Name *", self.name)
        self.form_layout.addRow("Surname *", self.surname)
        self.form_layout.addRow("JMBAG *", self.jmbag)
        self.form_layout.addRow("Session Name", self.session_name)
        self.form_layout.addWidget(self.required)

        # Create Buttons
        self.ok_btn = QtWidgets.QPushButton(self)
        self.ok_btn.setObjectName("ok_btn")
        self.ok_btn.setText("Ok")

        self.cancel_btn = QtWidgets.QPushButton(self)
        self.cancel_btn.setObjectName("cancel_btn")
        self.cancel_btn.setText("Cancel")

        # Set buttons in Horizontal Box
        # (it could be possible to use popup instead of QWidget so buttons are ordered according to os)
        self.h_box_layout = QHBoxLayout()
        self.h_box_layout.addWidget(self.cancel_btn)
        self.h_box_layout.addWidget(self.ok_btn)

        # Set Buttons under Form Layout
        self.v_box_layout = QVBoxLayout()
        self.v_box_layout.addLayout(self.form_layout)
        self.v_box_layout.addLayout(self.h_box_layout)

        # Set main layout (to Ui_Form - QWidget)
        self.setLayout(self.v_box_layout)

        # Translate UI
        # self.retranslateUi(self)

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

    def session_text_edited(self):
        if not self.session_text_edited_flag:
            self.session_text_edited_flag = True

    def update_session_name(self, text):
        if not self.session_text_edited_flag:
            # Concat name, surname and datetime
            final_name = ""
            final_name = final_name + self.name.text()
            final_name = final_name + "_" + self.surname.text()
            final_name = final_name + "_" + NetworkHelper.get_formatted_time(None)
            self.session_name.setText(final_name)

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
        is_success, data = NetworkHelper.add_user(self.name.text().strip(), self.surname.text().strip(),
                                                  self.jmbag.text(), int(self.record_num.text()))
        if not is_success or data is None:
            return False

        self.data = data
        self.data[u"record_length"] = int(self.record_length.text())
        self.data[u"number_of_records"] = int(self.record_num.text())
        return True

    def get_data(self):
        return self.data

    def showMessageBox(self, message):
        msg_box = QtWidgets.QMessageBox()
        msg_box.setText(message)
        msg_box.setIcon(QtWidgets.QMessageBox.Warning)
        msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg_box.exec_()

