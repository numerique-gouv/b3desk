import random
import re
import string

from flask import current_app
from flask import request
from netaddr import IPAddress
from netaddr import IPNetwork


def secret_key():
    return current_app.config["SECRET_KEY"]


def is_rie():
    """
    Checks wether the request was made from inside the state network
    "Réseau Interministériel de l’État"
    """
    if not request.remote_addr:
        return False

    return current_app.config["RIE_NETWORK_IPS"] and any(
        IPAddress(request.remote_addr) in IPNetwork(str(network_ip))
        for network_ip in current_app.config["RIE_NETWORK_IPS"]
        if network_ip
    )


def is_accepted_email(email):
    for regex in current_app.config["EMAIL_WHITELIST"]:
        if re.search(regex, email):
            return True
    return False


def is_valid_email(email):
    if not email or not re.search(
        r"^([a-zA-Z0-9_\-\.']+)@([a-zA-Z0-9_\-\.]+)\.([a-zA-Z]{2,5})$", email
    ):
        return False
    return True


def get_random_alphanumeric_string(length):
    letters_and_digits = string.ascii_letters + string.digits
    result_str = "".join(random.choice(letters_and_digits) for i in range(length))
    return result_str
