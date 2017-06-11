STATUS_OK = 200
STATUS_NO_CONTENT = 204
BASE_URL = ""
APP_SECRET = "some app secret"
FOLDER = ".get_pulse"
HOST_JSON_FILE = "host.json"
WINDOWS = "Windows"
delimiter = ""


def get_host(http, host, port):
    return "{0}://{1}:{2}/api/".format(http, host, port)
