import numpy as np
import cv2
import os
import sys
from datetime import datetime
import time


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class findFaceGetPulse(object):
    def __init__(self, bpm_limits=[], data_spike_limit=250,
                 face_detector_smoothness=10):

        self.frame_in = np.zeros((10, 10))
        self.frame_out = np.zeros((10, 10))
        self.fps = 0
        self.buffer_size = 250
        self.data_buffer = []
        self.times = []
        self.ttimes = []
        self.samples = []
        self.freqs = []
        self.fft = []
        self.slices = [[0]]
        self.t0 = time.time()
        self.bpms = []
        self.bpm = 0

        dpath = resource_path("haarcascade_frontalface_alt.xml")
        if not os.path.exists(dpath):
            print "Cascade file not present!"
        self.face_cascade = cv2.CascadeClassifier(dpath)

        self.face_rect = [1, 1, 2, 2]
        self.last_center = np.array([0, 0])
        self.last_wh = np.array([0, 0])
        self.output_dim = 13
        self.trained = False

        self.idx = 1
        self.find_faces = True
        self.counter = 0
        self.is_success = True

        self.time_gap = None

    def find_faces_toggle(self, data):
        self.find_faces = not self.find_faces
        self.start_time = self.get_current_time()
        self.end_time = data[u"record_length"] + self.start_time
        self.data = data
        self.heart_rates = []

        if self.is_success:
            self.counter = self.counter + 1
            self.is_success = False

        return self.find_faces

    def get_faces(self):
        return

    def shift(self, detected):
        x, y, w, h = detected
        center = np.array([x + 0.5 * w, y + 0.5 * h])
        shift = np.linalg.norm(center - self.last_center)

        self.last_center = center
        return shift

    def draw_rect(self, rect, col=(0, 255, 0)):
        x, y, w, h = rect
        cv2.rectangle(self.frame_out, (x, y), (x + w, y + h), col, 1)

    def get_subface_coord(self, fh_x, fh_y, fh_w, fh_h):
        x, y, w, h = self.face_rect
        return [int(x + w * fh_x - (w * fh_w / 2.0)),
                int(y + h * fh_y - (h * fh_h / 2.0)),
                int(w * fh_w),
                int(h * fh_h)]

    def get_subface_means(self, coord):
        x, y, w, h = coord
        subframe = self.frame_in[y:y + h, x:x + w, :]
        v1 = np.mean(subframe[:, :, 0])
        v2 = np.mean(subframe[:, :, 1])
        v3 = np.mean(subframe[:, :, 2])

        return (v1 + v2 + v3) / 3.

    def train(self):
        self.trained = not self.trained
        return self.trained

    # def plot(self):
    #     data = np.array(self.data_buffer).T
    #     np.savetxt("data.dat", data)
    #     np.savetxt("times.dat", self.times)
    #     freqs = 60. * self.freqs
    #     idx = np.where((freqs > 50) & (freqs < 180))
    #     pylab.figure()
    #     n = data.shape[0]
    #     for k in xrange(n):
    #         pylab.subplot(n, 1, k + 1)
    #         pylab.plot(self.times, data[k])
    #     pylab.savefig("data.png")
    #     pylab.figure()
    #     for k in xrange(self.output_dim):
    #         pylab.subplot(self.output_dim, 1, k + 1)
    #         pylab.plot(self.times, self.pcadata[k])
    #     pylab.savefig("data_pca.png")
    #
    #     pylab.figure()
    #     for k in xrange(self.output_dim):
    #         pylab.subplot(self.output_dim, 1, k + 1)
    #         pylab.plot(freqs[idx], self.fft[k][idx])
    #     pylab.savefig("data_fft.png")
    #     quit()

    def run(self, cam):
        """
        Function used to process single image received from camera
        """
        self.times.append(time.time() - self.t0)
        self.frame_out = self.frame_in
        self.gray = cv2.equalizeHist(cv2.cvtColor(self.frame_in,
                                                  cv2.COLOR_BGR2GRAY))
        col = (100, 255, 100)

        # if not measuring
        if self.find_faces:
            self.detect_face()
            return
        elif set(self.face_rect) == set([1, 1, 2, 2]):
            return
        # else: -> While measuring
        else:
            cv2.putText(
                self.frame_out, "Press 'A' to stop",
                (10, 25), cv2.FONT_HERSHEY_PLAIN, 1.5, col)
            # cv2.putText(self.frame_out, "Records: {0} / {1}".format(self.counter, self.data[u"number_of_records"]),
            #            (10, 75), cv2.FONT_HERSHEY_PLAIN, 1.5, col)
            cv2.putText(self.frame_out, "Press 'Esc' to quit",
                        (10, 50), cv2.FONT_HERSHEY_PLAIN, 1.5, col)

            forehead1 = self.get_subface_coord(0.5, 0.18, 0.25, 0.15)
            self.draw_rect(forehead1)

            vals = self.get_subface_means(forehead1)

            self.data_buffer.append(vals)
            L = len(self.data_buffer)
            # If Data Buffer length is greater than
            # specified Buffer size, discard oldest measurements
            if L > self.buffer_size:
                self.data_buffer = self.data_buffer[-self.buffer_size:]
                self.times = self.times[-self.buffer_size:]
                L = self.buffer_size

            processed = np.array(self.data_buffer)
            # self.samples are used for make_bpm_plot and write_csv
            self.samples = processed
            # If there are more than 10 measurements, calculate bpm
            if L > 10:
                self.output_dim = processed.shape[0]

                self.fps = float(L) / (self.times[-1] - self.times[0])
                even_times = np.linspace(self.times[0], self.times[-1], L)
                interpolated = np.interp(even_times, self.times, processed)
                interpolated = np.hamming(L) * interpolated
                interpolated = interpolated - np.mean(interpolated)
                raw = np.fft.rfft(interpolated)
                phase = np.angle(raw)
                self.fft = np.abs(raw)
                self.freqs = float(self.fps) / L * np.arange(L / 2 + 1)
                freqs = 60. * self.freqs
                idx = np.where((freqs > 50) & (freqs < 180))

                pruned = self.fft[idx]
                phase = phase[idx]

                pfreq = freqs[idx]
                self.freqs = pfreq
                self.fft = pruned
                if pruned.any():
                    idx2 = np.argmax(pruned)
                else:
                    return

                t = (np.sin(phase[idx2]) + 1.) / 2.
                t = 0.9 * t + 0.1
                alpha = t
                beta = 1 - t

                self.bpm = self.freqs[idx2]
                self.idx += 1

                x, y, w, h = self.get_subface_coord(0.5, 0.18, 0.25, 0.15)
                r = alpha * self.frame_in[y:y + h, x:x + w, 0]
                g = alpha * \
                    self.frame_in[y:y + h, x:x + w, 1] + \
                    beta * self.gray[y:y + h, x:x + w]
                b = alpha * self.frame_in[y:y + h, x:x + w, 2]
                self.frame_out[y:y + h, x:x + w] = cv2.merge([r, g, b])
                x1, y1, w1, h1 = self.face_rect
                self.slices = [np.copy(self.frame_out[y1:y1 + h1, x1:x1 + w1, 1])]

                #######################################################################################

                # get time gap to data[u"record_length"]
                self.time_gap = self.end_time - self.get_current_time()

                # "Fix" not to show remaining time
                self.time_gap = 0

                self.heart_rates.append(self.bpm)

                if self.time_gap:
                    text = "(estimate: %0.1f bpm, wait %0.0f s)" % (self.bpm, self.time_gap)
                else:
                    text = "(estimate: %0.1f bpm)" % (self.bpm)
                cv2.putText(self.frame_out, text,
                            (x - w / 2, y), cv2.FONT_HERSHEY_PLAIN, 1, col)

    def detect_face(self):
        col = (100, 255, 100)

        cv2.putText(self.frame_out, "Press 'S' to lock face and begin", (10, 25), cv2.FONT_HERSHEY_PLAIN, 1.25, col)
        cv2.putText(self.frame_out, "Press 'Esc' to quit", (10, 50), cv2.FONT_HERSHEY_PLAIN, 1.25, col)
        self.data_buffer, self.times, self.trained = [], [], False
        detected = list(self.face_cascade.detectMultiScale(self.gray,
                                                           scaleFactor=1.3,
                                                           minNeighbors=4,
                                                           minSize=(
                                                               50, 50),
                                                           flags=cv2.CASCADE_SCALE_IMAGE))

        if len(detected) > 0:
            detected.sort(key=lambda a: a[-1] * a[-2])

            if self.shift(detected[-1]) > 10:
                self.face_rect = detected[-1]
        forehead1 = self.get_subface_coord(0.5, 0.18, 0.25, 0.15)
        self.draw_rect(self.face_rect, col=(255, 0, 0))
        x, y, w, h = self.face_rect
        cv2.putText(self.frame_out, "Face",
                    (x, y), cv2.FONT_HERSHEY_PLAIN, 1.5, col)
        self.draw_rect(forehead1)
        x, y, w, h = forehead1
        cv2.putText(self.frame_out, "Forehead",
                    (x, y), cv2.FONT_HERSHEY_PLAIN, 1.5, col)

    def get_current_time(self):
        year = datetime.now().timetuple().tm_year
        month = datetime.now().timetuple().tm_mon
        day = datetime.now().timetuple().tm_mday
        hour = datetime.now().timetuple().tm_hour
        minute = datetime.now().timetuple().tm_min
        second = datetime.now().timetuple().tm_sec

        current = datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=second)
        return (current - datetime(1970, 1, 1)).total_seconds()
