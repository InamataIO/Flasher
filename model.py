import json
from typing import Any, Callable, Union

import keyring
import requests
from keyring.errors import PasswordDeleteError

from worker import WorkerInformation, WorkerWarning
from config import DSFlasherConfig


class DSFlasherModel:
    """Used to login to the DS server."""

    ds_domain = "localhost:8000"
    secure_url = False

    def __init__(self, config: DSFlasherConfig):
        self._config = config
        if self.secure_url:
            http_type = "https://"
        else:
            http_type = "http://"
        self.login_url = f"{http_type}{self.ds_domain}/accounts/login/"
        self.token_url = f"{http_type}{self.ds_domain}/api/v1/accounts/auth-token/"

    def log_in(self, username: str, password: str):
        """Log in to the DeviceStacc server and get an auth token."""
        try:
            data = {"username": username, "password": password}
            headers = {"Host": self.ds_domain}
            response = requests.post(self.token_url, data, headers=headers, timeout=10)
            response.raise_for_status()
            token = json.loads(response.content)["token"]
            self._save_credentials(username, token)
        except requests.exceptions.HTTPError as err:
            if err.response.status_code == 400:
                message = "Login credentials not correct. Please check your e-mail and password."
                raise WorkerInformation(message) from err
            else:
                raise WorkerWarning(str(err)) from err
        except requests.exceptions.ConnectionError as err:
            raise WorkerWarning(str(err)) from err
        except requests.exceptions.Timeout as err:
            raise WorkerWarning(str(err)) from err
        except requests.exceptions.RequestException as err:
            raise WorkerWarning(str(err)) from err

    def log_out(self):
        self._clear_credentials()

    def sign_up(self):
        print("Signing up!")

    def get_username(self) -> str:
        return self._config.config["username"]

    def is_authenticated(self) -> bool:
        username = self._config.config["username"]
        credential = keyring.get_credential(self._config.app_name, username)
        return bool(credential)

    def _save_credentials(self, username: str, token: str) -> None:
        """Save the auth token in a keychain."""
        self._config.config["username"] = username
        keyring.set_password(self._config.app_name, username, token)

    def _clear_credentials(self) -> None:
        """Clear the username and auth token"""
        username = self._config.config["username"]
        try:
            keyring.delete_password(self._config.app_name, username)
        except PasswordDeleteError:
            pass
