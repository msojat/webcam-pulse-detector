from lib.GUI_objects.MainWindow import MainWindow
import sys
import os
from os.path import expanduser
import platform
from PyQt5 import QtWidgets
import json
from constants import constants


def window():
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


    ########################
    #     UI Creation      #
    ########################
    app = QtWidgets.QApplication(sys.argv)

    main_window = MainWindow(config=data)
    main_window.show()

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
        json_content = json.loads('{ "http": "http", "host": "localhost", "port": "3000", '
                                  '"image_set_1_dir": "images/image_set_1", "image_set_2_dir": "images/image_set_2", '
                                  '"image_number":10, "image_time":30, "pause_time":10 }')
        json.dump(json_content, f)
        f.close()


if __name__ == "__main__":
    window()
