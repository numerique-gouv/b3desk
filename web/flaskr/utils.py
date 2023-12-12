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
