STATUS_OK = 200
STATUS_NO_CONTENT = 204
BASE_URL = "http://localhost:3000/api/"
APP_SECRET = "some_app_secret"
FOLDER = ".get_pulse"
CONFIG_JSON_FILE = "config.json"
WINDOWS = "Windows"
delimiter = ""


def get_host(http, host, port):
    return "{0}://{1}:{2}/api/".format(http, host, port)
