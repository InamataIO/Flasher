import json
from typing import Callable, Union
import requests

ds_domain = "localhost:8000"
secure_url = False


class DSFlasherModel:
    def __init__(self):
        if secure_url:
            http_type = "https://"
        else:
            http_type = "http://"
        self.login_url = f"{http_type}{ds_domain}/accounts/login/"
        self.token_url = f"{http_type}{ds_domain}/api/v1/accounts/auth-token/"

    def login(self, username: Union[str, Callable], password: Union[str, Callable]):
        """Log in to the DeviceStacc server and get an auth token."""
        # Support passing parameters as functions
        if callable(username):
            username = username()
        if callable(password):
            password = password()
        try:
            data = {"username": username, "password": password}
            headers = {"Host": ds_domain}
            response = requests.post(self.token_url, data, headers=headers)
            response.raise_for_status()
            token = json.loads(response.content)
            print(token)
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