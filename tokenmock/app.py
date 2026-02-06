#!/usr/bin/env python3

import json
import os
from pathlib import Path

import requests
from flask import Flask
from flask import current_app
from flask import jsonify
from flask import request

app = Flask(__name__)


def load_config():
    """Load configuration from environment and key file."""
    key_file_path = Path("conf/key.txt")
    try:
        with open(key_file_path) as f:
            nextcloud_sessiontoken_key = f.read().strip()
    except FileNotFoundError as exc:
        raise RuntimeError(f"Key file not found: {key_file_path}") from exc

    config = {
        "NC_LOGIN_API_KEY": os.environ.get("NC_LOGIN_API_KEY"),
        "NC_HOST": os.environ.get("NC_HOST"),
        "NEXTCLOUD_SESSIONTOKEN_KEY": nextcloud_sessiontoken_key,
    }

    if not config["NC_LOGIN_API_KEY"]:
        raise RuntimeError("NC_LOGIN_API_KEY environment variable is required")

    if not config["NC_HOST"]:
        raise RuntimeError("NC_HOST environment variable is required")

    return config


@app.route("/", methods=["POST"])
def token():
    """Handle token requests.

    Expects JSON payload with 'username' field.
    Requires X-API-KEY header for authentication.
    """
    try:
        config = load_config()
    except RuntimeError as exc:
        current_app.logger.error(f"Bad configuration: {exc}")
        return jsonify({"error": str(exc)}), 500

    api_key = request.headers.get("X-API-KEY")
    if not api_key or api_key != config["NC_LOGIN_API_KEY"]:
        return "Denied", 403

    try:
        data = request.get_json()
    except Exception:
        return jsonify({"error": "Invalid JSON payload"}), 400

    if not data or "username" not in data:
        return jsonify({"error": "Missing username in request"}), 400

    nextcloud_endpoint = f"{config['NC_HOST']}/apps/sessiontoken/token"
    payload = {
        "apikey": config["NEXTCLOUD_SESSIONTOKEN_KEY"],
        "name": "tokenmock",
        "user": data["username"],
    }

    try:
        response = requests.post(nextcloud_endpoint, data=payload, timeout=30)
        nc_data = response.json()

    except requests.exceptions.RequestException as exc:
        current_app.logger.error(f"Failed to connect to Nextcloud: {exc}")
        return jsonify({"error": f"Failed to connect to Nextcloud: {exc}"}), 500

    except json.JSONDecodeError as exc:
        current_app.logger.error(f"Invalid response from Nextcloud: {exc}")
        return jsonify({"error": "Invalid response from Nextcloud"}), 500

    if response.status_code != 200:
        current_app.logger.error(
            f"Invalid response from Nextcloud: {nc_data.get('message')}"
        )
        return jsonify(
            {"error": "Invalid response from Nextcloud"}
        ), response.status_code

    response_data = {
        "nctoken": nc_data.get("token"),
        "nclocator": config["NC_HOST"],
        "nclogin": data["username"],
    }

    return jsonify(response_data)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9000, debug=True)
