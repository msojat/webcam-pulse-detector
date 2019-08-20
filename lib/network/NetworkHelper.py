import json
import time

import requests

from constants import constants


class NetworkHelper:
    def __init__(self):
        pass

    @staticmethod
    def get_formatted_time(time_seconds):
        FMT = "%Y-%m-%d %H:%M:%S"
        return time.strftime(FMT, time.gmtime(time_seconds))

    @staticmethod
    def add_user(name, surname, jmbag, number_of_records):
        url = "{0}{1}".format(constants.BASE_URL, "add_user")
        body = {
            "name": name,
            "surname": surname,
            "jmbag": jmbag,
            "number_of_records": number_of_records,
            "app_secret": constants.APP_SECRET
        }

        try:
            response = requests.post(url=url, data=body)
            data = None

            if response.status_code == constants.STATUS_OK:
                # Response contains: identifier_id & user_id
                data = json.loads(response.text)
            return True, data

        except Exception as err:
            error_msg = "Connection refused" if "Connection refused" in str(err.message) \
                else str(err.message)
            print(error_msg)
            return False, None

    # TODO: Update or delete method
    @staticmethod
    def add_record(user_id, record_length, identifier_id, number_of_records, record_number,
                   start_record_time, end_record_time, heart_rate):
        url = "{0}{1}".format(constants.BASE_URL, "add_record")
        body = {
            "user_id": user_id,
            "record_length": record_length,
            "identifier_id": identifier_id,
            "number_of_records": number_of_records,
            "record_number": record_number,
            "start_record_time": start_record_time,
            "end_record_time": end_record_time,
            "heart_rate": heart_rate,
            "app_secret": constants.APP_SECRET
        }

        try:
            response = requests.post(url=url, data=body)

            if response.status_code == constants.STATUS_NO_CONTENT:
                return True, None
            return False, None

        except Exception as err:
            print(err.message)
            return False, None

    @staticmethod
    def add_record_bulk(session_id, records):
        url = "{0}{1}".format(constants.BASE_URL, "add_record/bulk")
        body = {
            "measurement_session_id": session_id,
            "records": records,
            "app_secret": constants.APP_SECRET
        }
        try:
            response = requests.post(url=url, json=body)

            if response.status_code == constants.STATUS_OK:
                return True, None
            return False, None

        except Exception as err:
            print(err.message)
            return False, None

    @staticmethod
    def add_image(image):
        url = "{0}{1}".format(constants.BASE_URL, "add_image")
        body = {
            "name": image['name'],
            "app_secret": constants.APP_SECRET
        }
        if hasattr(image, 'location'):
            body['location'] = image['location']

        try:
            response = requests.post(url=url, data=body)
            data = None

            if response.status_code == constants.STATUS_OK:
                data = json.loads(response.text)
                return True, data
            return False, data

        except Exception as err:
            error_msg = "Connection refused" if "Connection refused" in str(err.message) \
                else str(err.message)
            print(error_msg)
            return False, None

    @staticmethod
    def create_measurement_session(user_id):
        url = "{0}{1}".format(constants.BASE_URL, "session")
        body = {
            "app_secret": constants.APP_SECRET,
            "user_id": user_id,
            "start_time": NetworkHelper.get_formatted_time(time.time())

        }

        try:
            response = requests.post(url=url, data=body)

            if response.status_code == constants.STATUS_OK:
                data = json.loads(response.text)
                measurement_session_id = data['measurement_session_id']
                return True, measurement_session_id
            return False, None

        except Exception as err:
            error_msg = "Connection refused" if "Connection refused" in str(err.message) \
                else str(err.message)
            print(error_msg)
            return False, None
