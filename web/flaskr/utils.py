import git
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

    return any(
        IPAddress(request.remote_addr) in IPNetwork(network_ip)
        for network_ip in current_app.config.get("RIE_NETWORK_IPS", [])
        if network_ip
    )


def get_git_commit():  # pragma: no cover
    try:
        repo = git.Repo(search_parent_directories=True)
        sha = repo.head.commit.hexsha
        short_sha = repo.git.rev_parse(sha, short=4)
        return short_sha

    except git.exc.GitError:
        return None


def get_git_tag():  # pragma: no cover
    try:
        repo = git.Repo(search_parent_directories=True)
        tag = next((tag for tag in repo.tags if tag.commit == repo.head.commit), None)
        if tag:
            return tag.name

    except git.exc.GitError:
        return None
