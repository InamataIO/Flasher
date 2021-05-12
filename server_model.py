import hashlib
import json
import logging
import os
import time
from typing import List
from urllib.parse import urlparse

import keyring
import requests
from keyring.errors import PasswordDeleteError
from semantic_version import Version

from config import Config
from worker import WorkerInformation, WorkerWarning


class ServerModel:
    """Used to login to the DS server."""

    ds_domain = "localhost:8000"
    secure_url = False
    default_partition_table_name = "min_spiffs"
    default_partition_table_id = ""

    def __init__(self, config: Config):
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
        response = self._auth_server_request(self.graphql_url, data)
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
                        id, siteEntity {{ name }}, authToken {{ key }},
                        partitionTable {{ id }}, firmwareImage {{ id }}
                    }} }}
                }}
            }}
            """,
            "variables": None,
        }
        response = self._auth_server_request(self.graphql_url, data)
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

    def get_default_partition_table(self) -> dict:
        """Try to get the default partition table."""
        if partition_table := self._get_cached_partition_table(
            self.default_partition_table_id
        ):
            return partition_table

        # Search for the partition table from the server
        partition_table_name = self.default_partition_table_name
        data = {
            "query": f"""
            {{
                allControllerPartitionTables(
                    name: "{partition_table_name}", isGlobal: true, first: 1
                ) {{
                    edges {{ node {{
                        id, name, table
                    }} }}
                }}
            }}
            """,
            "variables": None,
        }
        response = self._auth_server_request(self.graphql_url, data)
        output = json.loads(response.content)
        if errors := output.get("errors"):
            logging.warning(errors)
            raise WorkerWarning("Error while getting default partition table data.")
        results = output["data"]["allControllerPartitionTables"]["edges"]
        partition_tables = [i["node"] for i in results]
        if not partition_tables:
            raise WorkerWarning(
                f"Could not find default partition table ({partition_table_name})"
            )
        partition_table_id = partition_tables[0]["id"]
        self.default_partition_table_id = partition_table_id
        self._cache_partition_table(partition_table_id, partition_tables[0])
        return partition_tables[0]

    def get_partition_table(self, partition_table_id: dict) -> dict:
        """Gets the partition table for a given controller."""
        if partition_table := self._get_cached_partition_table(partition_table_id):
            return partition_table

        # Fetch the partition table from the server
        data = {
            "query": f"""
            {{
                controllerPartitionTable(id: "{partition_table_id}") {{
                    id, name, table
                }}
            }}
            """,
            "variables": None,
        }
        response = self._auth_server_request(self.graphql_url, data)
        output = json.loads(response.content)
        if errors := output.get("errors"):
            logging.warning(errors)
            raise WorkerWarning("Error while getting partition table data.")
        partition_table = output["data"]["controllerPartitionTable"]
        # Check if the partition table was found on the server
        if not partition_table:
            raise WorkerWarning("Could not find partition table on server.")
        self._cache_partition_table(partition_table_id, partition_table)
        return partition_table

    def register_controller(
        self, name, site_id, controller_type_id, firmware_image_id, **kwargs
    ) -> dict:
        """Create and register a controller on the server."""
        partition_table = self.get_default_partition_table()
        data = {
            "query": """
            mutation createControllerComponent($input: CreateControllerComponentInput!) {
                createControllerComponent(input: $input) {
                    controllerComponent {
                        id, siteEntity { name }, authToken { key },
                        partitionTable { id }, firmwareImage { id }
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
                        "partitionTable": partition_table["id"],
                        "firmwareImage": firmware_image_id,
                    }
                }
            ),
        }
        response = self._auth_server_request(self.graphql_url, data)
        output = json.loads(response.content)
        if errors := output.get("errors"):
            raise WorkerInformation(errors[0]["message"])
        controllers = self._config.config.get("controllers", [])
        controller = output["data"]["createControllerComponent"]["controllerComponent"]
        controllers.append(controller)
        return controller

    def get_username(self) -> str:
        return self._config.config.get("username", "")

    def is_authenticated(self) -> bool:
        return bool(self._auth_token)

    def download_firmware_image(self, firmware_id: str, **kwargs) -> dict:
        """Download the selected firmware if it is not cached locally."""
        try:
            firmwares = self._config.config["firmwareImages"]
            firmware = next(i for i in firmwares if i["id"] == firmware_id)
            path = self.get_firmware_image_path(firmware)
            # If the file has been downloaded to the cache and has the same hash, return
            if self._is_file_valid(path, firmware["hashSha3_512"]):
                return firmware
            # Download the file and notify of progress
            os.makedirs(self._config.dirs.user_cache_dir, exist_ok=True)
            with open(path, "wb+") as f:
                progress_callback = kwargs["progress_callback"]
                # If the download link has expired, request a new one and retry
                response = requests.get(firmware["file"], stream=True)
                if response.status_code >= 400:
                    self._refresh_firmware_image_url(firmware)
                    response = requests.get(firmware["file"], stream=True)
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
            if not self._is_file_valid(path, firmware["hashSha3_512"]):
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
        return firmware

    def get_firmware_image_path(self, firmware_image) -> str:
        """Returns the absolute path to the firmware image."""
        parse_result = urlparse(firmware_image["file"])
        filename = os.path.basename(parse_result.path)
        return os.path.join(self._config.dirs.user_cache_dir, filename)

    def get_firmware_image(self, firmware_image_id: str) -> dict:
        """Returns the firmware image for a given ID."""
        firmware_image = next(
            i
            for i in self._config.config.get("firmwareImages")
            if i["id"] == firmware_image_id
        )
        return firmware_image

    @staticmethod
    def _is_file_valid(file_path: str, sha3_512_hash: str) -> bool:
        """Check if the file's hash matches the supplied hash."""
        try:
            with open(file_path, "rb") as f:
                file_hash = hashlib.sha3_512(f.read()).hexdigest()
        except FileNotFoundError:
            file_hash = ""
        return sha3_512_hash == file_hash

    def _get_cached_partition_table(self, partition_table_id) -> dict:
        """Try to get the cached partition table. Empty dict on cache miss."""
        try:
            partition_table = self._config.config["partitionTables"][partition_table_id]
            return partition_table
        except KeyError:
            return {}

    def _cache_partition_table(self, partition_table_id, partition_table) -> None:
        """Store the partition table in the cache."""
        try:
            partition_tables = self._config.config["partitionTables"]
        except KeyError:
            partition_tables = {}
        partition_tables.update({partition_table_id: partition_table})

    def _refresh_firmware_image_url(self, firmware_image):
        """Refresh the (expired) URL of a firmware image."""
        data = {
            "query": f"""
            {{
                firmwareImage(id: "{firmware_image['id']}") {{
                    id, name, version, file, hashSha3_512
                }}
            }}""",
            "variables": None,
        }
        response = self._auth_server_request(self.graphql_url, data)
        output = json.loads(response.content)
        if errors := output.get("errors"):
            logging.warning(errors)
            raise WorkerWarning(
                "Error while refreshing the firmware URL. Please reload data."
            )
        firmware_image["file"] = output["data"]["firmwareImage"]["file"]

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

    def _auth_server_request(self, url, data, headers=None):
        """Make a GraphQL server request with the cached auth token."""
        if not headers:
            headers = {**self._default_headers}
        headers = {**headers, "Authorization": f"Token {self._auth_token}"}
        return self._server_request(url, data, headers)

    def _server_request(self, url, data, headers=None):
        """Make a GraphQL server request that handles HTTP errors."""
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
