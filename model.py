import json
import os
import pathlib
from json import JSONDecodeError
from typing import Any, Callable, Union

import keyring
import requests
from appdirs import AppDirs
from keyring.errors import PasswordDeleteError

from worker import WorkerInformation, WorkerWarning


class DSFlasherModel:
    """Used to login to the DS server."""

    ds_domain = "localhost:8000"
    secure_url = False
    app_name = "ds-flasher"
    app_author = "device-stacc"
    dirs = AppDirs(app_name, app_author)

    def __init__(self):
        if self.secure_url:
            http_type = "https://"
        else:
            http_type = "http://"
        self.login_url = f"{http_type}{self.ds_domain}/accounts/login/"
        self.token_url = f"{http_type}{self.ds_domain}/api/v1/accounts/auth-token/"
        pathlib.Path(self.dirs.user_config_dir).mkdir(parents=True, exist_ok=True)
        self.config_path = os.path.join(self.dirs.user_config_dir, "config.json")

    def log_in(
        self,
        username: Union[str, Callable],
        password: Union[str, Callable],
        **kwargs,
    ):
        """Log in to the DeviceStacc server and get an auth token."""
        # Support passing parameters as functions
        if callable(username):
            username = username()
        if callable(password):
            password = password()
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

    def get_saved_username(self) -> str:
        return self._get_config().get("username", "")

    def is_authenticated(self) -> bool:
        username = self.get_saved_username()
        credential = keyring.get_credential(self.app_name, username)
        return bool(credential)

    def _save_credentials(self, username, token):
        """Save the auth token in a keychain."""
        self._update_config_key("username", username)
        keyring.set_password(self.app_name, username, token)

    def _clear_credentials(self):
        """Clear the username and auth token"""
        username = self._get_config()["username"]
        try:
            keyring.delete_password(self.app_name, username)
        except PasswordDeleteError:
            pass

    def _get_config(self) -> dict:
        """Gets the stored config."""
        config = {}
        try:
            with open(self.config_path, "r") as file:
                config = json.load(file)
        except FileNotFoundError:
            pass
        return config

    def _save_config(self, config: dict) -> None:
        """Overwrites the config file."""
        with open(self.config_path, "w") as file:
            json.dump(config, file)

    def _update_config_key(self, key: str, value: Any) -> None:
        """Update a key in the config with the given value. If the config is troubled, it is cleared."""
        with open(self.config_path, "w+") as file:
            try:
                config = json.load(file)
            except JSONDecodeError:
                config = {}
            config[key] = value
            json.dump(config, file)

    def _clear_config_key(self, key: str) -> None:
        """Remove a key in the config."""
        with open(self.config_path, "w+") as file:
            try:
                config = json.load(file)
            except JSONDecodeError:
                return
            config.pop(key, None)
            json.dump(config, file)
