import json
import socket

def get_ip():
    # https://stackoverflow.com/a/28950776
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        # doesn't even have to be reachable
        s.connect(('10.254.254.254', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

import socket

def truthy(value):
    """
    Function to check if a value is truthy or falsy

    :param value: Input to check
    :return bool:
    """
    if value:
        if value.isdigit():
            if not float(value):
                return False
        if value == "False":
            return False
        try:
            if not json.loads(value):
                # Account for empty objects
                return False
        except json.JSONDecodeError:
            return True
    return False

def has_internet_connection():
    try:
        # connect to the host -- tells us if the host is actually
        # reachable
        socket.create_connection(("1.1.1.1", 53))
        return True
    except OSError:
        pass
    return False

