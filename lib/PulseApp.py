import datetime
import socket
import sys
import time

import numpy as np
from PyQt5.QtCore import QObject, pyqtSignal
from serial import Serial

from lib.device import Camera
from lib.interface import destroyWindow, moveWindow, plotXY, waitKey
from lib.network.NetworkHelper import NetworkHelper
from lib.processors_noopenmdao import findFaceGetPulse


class PulseApp(QObject):
    """
    Python application that finds a face in a webcam stream, then isolates the
    forehead.

    Then the average green-light intensity in the forehead region is gathered
    over time, and the detected person's pulse is estimated.
    """

    measurement_signal = pyqtSignal()

    def __init__(self, args, parent=None):
        super(PulseApp, self).__init__(parent=parent)

        self.bpm = 0

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

    def start_measuring(self):
        self.processor.find_faces = False
        self.processor.start_time = self.processor.get_current_time()
        self.processor.end_time = self.data[u"record_length"] + self.processor.start_time
        self.processor.data = self.data
        self.processor.heart_rates = []

    def stop_measuring(self):
        self.processor.find_faces = True
        self.processor.bpm = 0
        if self.processor.is_success:
            self.processor.counter += 1
            self.processor.is_success = False

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
            self.close()
            sys.exit()

        for key in self.key_controls.keys():
            if chr(self.pressed) == key:
                self.key_controls[key]()

    def main_loop(self):
        """
        Single iteration of the application's main loop.
        """

        #################
        # Image Process #
        #################
        # Get next image frame from the camera
        frame = self.cameras[self.selected_cam].get_frame()
        self.h, self.w, _c = frame.shape

        # set current image frame to the processor's input
        self.processor.frame_in = frame
        # process the image frame to perform all needed analysis
        self.processor.run(self.selected_cam)
        # self.processor.frame_out is accessed directly for displaying

        ################
        # Data Process #
        ################
        if self.processor.bpm != 0:
            self.bpm = self.processor.bpm
            self.measurement_signal.emit()

        """
        # Record length condition checking
        
        if self.processor.time_gap is not None and self.processor.time_gap <= 0:
            self.upload_measurements()
            self.processor.time_gap = None
        """

        ###############
        # Unused Part #
        ###############
        # create and/or update the raw data display if needed
        if self.bpm_plot:
            self.make_bpm_plot()

        if self.send_serial:
            self.serial.write(str(self.processor.bpm) + "\r\n")

        if self.send_udp:
            self.sock.sendto(str(self.processor.bpm), self.udp)

    def upload_measurements(self):
        is_success, _ = NetworkHelper.add_record(int(self.data[u"user_id"]), int(self.data[u"record_length"]),
                                 int(self.data[u"identifier_id"]), int(self.data[u"number_of_records"]),
                                 self.processor.counter, self.get_formatted_time(self.processor.start_time),
                                 self.get_formatted_time(self.processor.end_time),
                                 "{:.2f}".format(np.average(self.processor.heart_rates)))
        if not is_success:
            return

        else:
            self.avgData.append(int(np.average(self.processor.heart_rates)))

            self.processor.is_success = True

            # if self.processor.counter == self.data[u"number_of_records"]:
            #    self.showMessageBox("Average heart rate " + "{:.2f}".format(np.average(self.avgData)))

            # simulate "s" key pressed to end recording
            # pyautogui.press("s")
            # End recording
            self.toggle_search()

    def get_measurement(self):
        return self.bpm

    def setAppData(self, data):
        self.data = data
        self.avgData = []

    def get_formatted_time(self, time_seconds):
        FMT = "%Y-%m-%d %H:%M:%S"
        return time.strftime(FMT, time.gmtime(time_seconds))

    def close(self):
        try:
            self.measurement_signal.disconnect()
        except Exception:
            print("Signal in PulseApp was not connected.")
        
        for cam in self.cameras:
            cam.cam.release()
        if self.send_serial:
            self.serial.close()
        print("Closed Pulse App")
