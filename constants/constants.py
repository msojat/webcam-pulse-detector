import json
import os

STATUS_OK = 200
STATUS_NO_CONTENT = 204
BASE_URL = "http://localhost:3000/api/"


def get_app_secret():
    with open(os.path.abspath(__file__ + "/../../../config.json")) as config:
        data = json.load(config)
        return data["app_secret"]
