import json
from json import JSONDecodeError
import pathlib
import os
from typing import Any, Callable, Union
import requests
import keyring
from appdirs import AppDirs

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

    def login(self, username: Union[str, Callable], password: Union[str, Callable]):
        """Log in to the DeviceStacc server and get an auth token."""
        # Support passing parameters as functions
        if callable(username):
            username = username()
        if callable(password):
            password = password()
        try:
            data = {"username": username, "password": password}
            headers = {"Host": self.ds_domain}
            response = requests.post(self.token_url, data, headers=headers)
            response.raise_for_status()
            token = json.loads(response.content)["token"]
            print(token)
            self._save_auth_token(username, token)
        except requests.exceptions.HTTPError as errh:
            print("Http Error:", errh)
        except requests.exceptions.ConnectionError as errc:
            print("Error Connecting:", errc)
        except requests.exceptions.Timeout as errt:
            print("Timeout Error:", errt)
        except requests.exceptions.RequestException as err:
            print("OOps: Something Else", err)

    def sign_up(self):
        print("Signing up!")
    
    def _save_auth_token(self, username, token):
        """Save the auth token in a keychain."""
        self._update_config("username", username)        
        keyring.set_password("ds_flasher", username, token)
    
    def _get_config(self) -> dict:
        """Gets the stored config."""
        config = {}
        config_path = os.path.join(self.dirs.user_config_dir, "config.json")
        with open(config_path, "r") as file:
            config = json.load(file)
        return config
    
    def _save_config(self, config) -> None:
        """Overwrites the config file."""
        config_path = os.path.join(self.dirs.user_config_dir, "config.json")
        with open(config_path, "w") as file:
            json.dump(config, file)

    def _update_config(self, key: str, value: Any) -> None:
        """Update a key in the config with the given value. If the config is troubled, it is cleared."""
        config_path = os.path.join(self.dirs.user_config_dir, "config.json")
        with open(config_path, "w+") as file:
            try:
                config = json.load(file)
            except JSONDecodeError:
                config = {}
            config[key] = value
            json.dump(config, file)