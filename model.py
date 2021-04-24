import json
import logging
import time

import keyring
import requests
from keyring.errors import PasswordDeleteError
from semantic_version import Version

from config import DSFlasherConfig
from worker import WorkerInformation, WorkerWarning


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
        self.token_url = f"{http_type}{self.ds_domain}/api/v1/accounts/auth-token/"
        self.graphql_url = f"{http_type}{self.ds_domain}/graphql/"
        self._default_headers = {"Host": self.ds_domain}
        # Get auth token if it has been retrieved and saved
        self._auth_token = ""
        if username := self._config.config.get("username"):
            self._auth_token = keyring.get_password(self._config.app_name, username)

    def log_in(self, username: str, password: str, **kwargs):
        """Log in to the DeviceStacc server and get an auth token."""
        data = {"username": username, "password": password}
        response = self._server_request(self.token_url, data)
        token = json.loads(response.content)["token"]
        self._save_credentials(username, token)

    def log_out(self):
        self._clear_credentials()

    def sign_up(self):
        print("Signing up!")

    def get_site_and_firmware_data(self, **kwargs):
        """Get the available sites and firmware images."""
        data = {
            "query": """
            { 
                allFirmwareImages {
                    edges { node {
                        id, name, version, file
                    } } 
                }
                allSites {
                    edges { node {
                        id, name
                    } }
                }
            }""",
            "variables": None,
        }
        headers = {
            **self._default_headers,
            "Authorization": f"Token {self._auth_token}",
        }
        response = self._server_request(self.graphql_url, data, headers=headers)
        output = json.loads(response.content)
        if errors := output.get("errors"):
            print(errors)
            raise WorkerWarning("Error while getting site and firmware data.")
        firmware_images = [
            i["node"] for i in output["data"]["allFirmwareImages"]["edges"]
        ]
        firmware_images.sort(key=lambda x: Version(x["version"]), reverse=True)
        self._config.config["firmware_images"] = firmware_images
        sites = [i["node"] for i in output["data"]["allSites"]["edges"]]
        self._config.config["sites"] = sites

    def get_controller_data(self, site_id, **kwargs):
        """Get the available controllers for a given site."""
        if not site_id:
            logging.info("get_controller_data called without site")
            return
        data = {
            "query": f"""
            {{
                allControllerComponents(siteEntity_Site: "{site_id}") {{
                    pageInfo {{ hasNextPage }}
                    edges {{ node {{
                        id, siteEntity {{ name }}, authToken {{ key }}
                    }} }}
                }}
            }}
            """,
            "variables": None,
        }
        headers = {
            **self._default_headers,
            "Authorization": f"Token {self._auth_token}",
        }
        response = self._server_request(self.graphql_url, data, headers=headers)
        output = json.loads(response.content)
        if errors := output.get("errors"):
            print(errors)
            raise WorkerWarning("Error while getting controller data.")
        results = output["data"]["allControllerComponents"]
        if results["pageInfo"]["hasNextPage"]:
            message = (
                "Not all controllers for this site could be fetched. Please upgrade your DS"
                "Flasher tool."
            )
            raise WorkerInformation(message)
        try:
            controllers = [i["node"] for i in results["edges"]]
        except KeyError:
            controllers = []
        controllers.sort(key=lambda x: x["siteEntity"]["name"], reverse=True)

        if "controllers" not in self._config.config:
            self._config.config["controllers"] = {}
        self._config.config["controllers"].update({site_id: controllers})

    def get_username(self) -> str:
        return self._config.config.get("username", "")

    def is_authenticated(self) -> bool:
        return bool(self._auth_token)

    def _save_credentials(self, username: str, token: str) -> None:
        """Save the auth token in a keychain."""
        self._config.config["username"] = username
        self._auth_token = token
        keyring.set_password(self._config.app_name, username, token)

    def _clear_credentials(self) -> None:
        """Clear the username and auth token"""
        username = self._config.config["username"]
        try:
            keyring.delete_password(self._config.app_name, username)
        except PasswordDeleteError:
            pass

    def _server_request(self, url, data, headers=None):
        time.sleep(1.3)
        if not headers:
            headers = self._default_headers
        try:
            response = requests.post(url, data, headers=headers, timeout=10)
            response.raise_for_status()
            return response
        except requests.exceptions.HTTPError as err:
            if err.response.status_code == 400 and err.request.url == self.token_url:
                message = "Login credentials not correct. Please check your e-mail and password."
                raise WorkerInformation(message) from err
            if err.response.status_code == 400 and err.request.url == self.graphql_url:
                logging.debug()
                message = (
                    "An error occured while requesting data from the server API."
                    " Check that you're using an up-to-date version of the DS Flasher tool"
                )
                raise WorkerWarning(message) from err
            if err.response.status_code == 401:
                message = "Invalid authentication token. Please log in again."
                raise WorkerInformation(message) from err
            raise WorkerWarning(str(err)) from err
        except requests.exceptions.ConnectionError as err:
            error_type = type(err.args[0]).__name__
            message = f"Failed connecting to server: {error_type}"
            raise WorkerWarning(message) from err
        except requests.exceptions.Timeout as err:
            raise WorkerWarning(str(err)) from err
        except requests.exceptions.RequestException as err:
            raise WorkerWarning(str(err)) from err
