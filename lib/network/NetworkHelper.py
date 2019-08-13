import json

import requests

from constants import constants


class NetworkHelper:
    def __init__(self):
        pass

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
