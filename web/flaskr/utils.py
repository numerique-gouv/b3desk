from flask import current_app
from flask import request
from netaddr import IPAddress
from netaddr import IPNetwork


def secret_key():
    return current_app.config["SECRET_KEY"]


def retry_join_meeting(referrer, role, fullname, fullname_suffix):
    return bool(
        (referrer and "/meeting/wait/" in referrer)
        or (role in ("attendee", "moderator") and fullname)
        or (role == "authenticated" and fullname and fullname_suffix)
    )


def is_rie():
    """
    Checks wether the request was made from inside the state network
    "Réseau Interministériel de l’État"
    """
    if not request.remote_addr:
        return False

    return any(
        IPAddress(request.remote_addr) in IPNetwork(network_ip)
        for network_ip in current_app.config.get("RIE_NETWORK_IPS", [])
        if network_ip
    )
