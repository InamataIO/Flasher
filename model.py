import hashlib
import json
import logging
import os
import time
from typing import List
from urllib.parse import urlparse
from wifi_model import DSFlasherWiFiModel

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

    def log_in(self, username: str, password: str, **kwargs) -> None:
        """Log in to the DeviceStacc server and get an auth token."""
        data = {"username": username, "password": password}
        response = self._server_request(self.token_url, data)
        token = json.loads(response.content)["token"]
        self._save_credentials(username, token)

    def log_out(self) -> None:
        self._clear_credentials()

    def sign_up(self) -> None:
        print("Signing up!")

    def get_site_and_firmware_data(self, **kwargs) -> None:
        """Get the available sites and firmware images."""
        data = {
            "query": """
            { 
                allFirmwareImages {
                    edges { node {
                        id, name, version, file, hashSha3_512
                    } } 
                }
                allSites {
                    edges { node {
                        id, name
                    } }
                }
                allControllerComponentTypes(isGlobal: true, name: "ESP32") {
                    edges { node {
                        id, name, isGlobal
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
            logging.warning(errors)
            raise WorkerWarning("Error while getting site and firmware data.")
        firmware_images = [
            i["node"] for i in output["data"]["allFirmwareImages"]["edges"]
        ]
        firmware_images.sort(key=lambda x: Version(x["version"]), reverse=True)
        self._config.config["firmwareImages"] = firmware_images
        sites = [i["node"] for i in output["data"]["allSites"]["edges"]]
        self._config.config["sites"] = sites
        controller_types = [
            i["node"] for i in output["data"]["allControllerComponentTypes"]["edges"]
        ]
        self._config.config["controllerComponentTypes"] = controller_types

    def get_controller_data(self, site_id: str, **kwargs) -> None:
        """Get the available controllers for a given site."""
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
            logging.warning(errors)
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

    def register_controller(self, name, site_id, controller_type_id, **kwargs):
        data = {
            "query": """
            mutation createControllerComponent($input: CreateControllerComponentInput!) {
                createControllerComponent(input: $input) {
                    controllerComponent {
                        id, siteEntity { name }, authToken { key }
                    }
                }
            }
            """,
            "variables": json.dumps(
                {
                    "input": {
                        "name": name,
                        "site": site_id,
                        "controllerType": controller_type_id,
                    }
                }
            ),
        }
        headers = {
            **self._default_headers,
            "Authorization": f"Token {self._auth_token}",
        }
        response = self._server_request(self.graphql_url, data, headers=headers)
        output = json.loads(response.content)
        raise NotImplementedError("Model.register_controller not implemented yet")

    def get_username(self) -> str:
        return self._config.config.get("username", "")

    def is_authenticated(self) -> bool:
        return bool(self._auth_token)

    def download_firmware_image(self, firmware_image, **kwargs) -> dict:
        """Download the selected firmware if it is not cached locally."""
        try:
            filename = self._derive_firmware_image_filename(firmware_image)
            path = os.path.join(self._config.dirs.user_cache_dir, filename)
            # If the file has been downloaded to the cache and has the same hash, return
            if self._is_file_valid(path, firmware_image["hashSha3_512"]):
                return firmware_image
            if not self._has_url_expired(firmware_image["file"]):
                self._refresh_firmware_image_data(firmware_image["id"])
            # Download the file and notify of progress
            os.makedirs(self._config.dirs.user_cache_dir, exist_ok=True)
            with open(path, "wb+") as f:
                progress_callback = kwargs["progress_callback"]
                response = requests.get(firmware_image["file"], stream=True)
                total_length = response.headers.get("content-length")
                # If the total length is unknown, skip notifying progress
                if total_length is None:
                    progress_callback(-1)
                    f.write(response.content)
                else:
                    received_bytes = 0
                    total_length = int(total_length)
                    for data in response.iter_content(chunk_size=64 * 1024):
                        f.write(data)
                        received_bytes += len(data)
                        percentage_done = int(100 * received_bytes / total_length)
                        progress_callback.emit(percentage_done)
            # Check the file hash. Delete and inform the user if it fails
            if not self._is_file_valid(path, firmware_image["hashSha3_512"]):
                os.remove(path)
                raise WorkerWarning(
                    "Checksum of downloaded file did not match. Please try another"
                    " version or contact support."
                )
        except KeyError as err:
            message = (
                f"Error downloading firmware. Not all required metadata found ({err})."
            )
            raise WorkerWarning(message)
        return firmware_image

    def flash_controller(
        self, firmware: dict, wifi_aps: List[DSFlasherWiFiModel.AP], **kwargs
    ):
        progress_callback = kwargs["progress_callback"]
        for i in range(1, 101):
            time.sleep(0.1)
            progress_callback.emit(i)

    @staticmethod
    def _derive_firmware_image_filename(firmware_image):
        """Creates a filename with the schema <name>_v<version>.<ext>"""
        path = urlparse(firmware_image["file"])
        filename = os.path.basename(path.path)
        extension = os.path.splitext(filename)
        return f"{firmware_image['name']}_v{firmware_image['version']}{extension[1]}"

    @staticmethod
    def _is_file_valid(file_path: str, sha3_512_hash: str) -> bool:
        try:
            with open(file_path, "rb") as f:
                file_hash = hashlib.sha3_512(f.read()).hexdigest()
        except FileNotFoundError:
            file_hash = ""
        return sha3_512_hash == file_hash

    def _has_url_expired(self, url):
        """Check if the access key of the pre-signed URL is still valid."""
        raise NotImplementedError("Model._has_url_expired not implemented yet")
    
    def _refresh_firmware_image_data(self, firmware_image_id):
        """Refresh metadata and (expired) URL of a firmware image."""
        raise NotImplementedError("Model._refresh_firmware_image_data not implemented yet")

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
            import ipdb; ipdb.set_trace()
            if err.response.status_code == 400 and err.request.url == self.token_url:
                message = "Login credentials not correct. Please check your e-mail and password."
                raise WorkerInformation(message) from err
            if err.response.status_code == 400 and err.request.url == self.graphql_url:
                logging.info(f"GraphQL error: {err.response.content}")
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
