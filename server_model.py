import hashlib
import json
import logging
import os
import webbrowser
from datetime import datetime, timedelta, timezone
from functools import cached_property
from time import sleep
from typing import Callable, Dict, List, Optional
from urllib.parse import urlparse

import jwt
import keyring
import requests
from keyring.errors import KeyringError, PasswordDeleteError
from semantic_version import Version

from config import Config, ControllerModel, SiteModel
from worker import WorkerError, WorkerInformation, WorkerWarning


class ServerModel:
    """Used to login to the Inamata server."""

    _core_base_url = "https://core.staging.inamata.co"
    _core_graphql_path = "/graphql/"

    _oauth_client_id = "flasher"
    _oauth_base_url = "https://auth.staging.inamata.co"
    _oauth_realm = "inamata"
    _oauth_device_path = (
        f"/auth/realms/{_oauth_realm}/protocol/openid-connect/auth/device"
    )
    _oauth_token_path = f"/auth/realms/{_oauth_realm}/protocol/openid-connect/token"
    _openid_config_path = (
        f"/auth/realms/{_oauth_realm}/.well-known/openid-configuration"
    )
    _openid_profile_keys = ["name", "email", "given_name", "family_name"]
    _access_token_audience = ["core-service", "account"]
    _refresh_token_audience = f"{_oauth_base_url}/auth/realms/{_oauth_realm}"

    _default_partition_table_name = "min_spiffs"
    _default_partition_table_id = ""

    @property
    def core_domain(self) -> str:
        return urlparse(self._core_base_url).hostname

    @property
    def is_core_url_secure(self) -> str:
        return urlparse(self._core_base_url).scheme == "https"

    def __init__(self, config: Config):
        self._config: Config = config
        self._oauth_access_token_cache: str = ""
        self._oauth_access_token_data_cache: Dict = {}
        self._oauth_refresh_token_cache: str = ""
        self._oauth_refresh_token_data_cache: Dict = {}

    def log_in(self, **kwargs) -> None:
        """Log in to the DeviceStacc server and get an auth token."""

        data = {"client_id": self._oauth_client_id, "scope": "offline_access"}
        headers = {"content-type": "application/x-www-form-urlencoded"}
        response = self._server_request(self._oauth_device_url, data, headers=headers)
        device_auth = response.json()
        # Open the web browser so that the user can log in and authorize the request
        webbrowser.open(device_auth["verification_uri_complete"])

        data = {
            "client_id": self._oauth_client_id,
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "device_code": device_auth["device_code"],
        }
        while True:
            # Poll for the access token with the given period
            sleep(device_auth["interval"])
            try:
                response = self._server_request(
                    self._oauth_token_url, data, headers=headers, raise_for_status=False
                )
                response.raise_for_status()
            except requests.exceptions.HTTPError as err:
                reply = err.response.json()
                if reply["error"] == "slow_down":
                    logging.info("Device auth polling too fast")
                elif reply["error"] == "authorization_pending":
                    logging.debug("Device authorization pending")
                elif reply["error"] == "invalid_grant":
                    raise WorkerWarning("Log in process timed out") from err
                elif reply["error"] == "access_denied":
                    raise WorkerWarning(
                        "Did not receive access from authentication service. Please try again and grant access in the browser prompt."
                    ) from err
                else:
                    raise WorkerWarning(reply["error_description"]) from err
                continue
            break

        tokens = response.json()
        self._save_credentials(tokens["access_token"], tokens["refresh_token"])
        self._store_token_profile(self._oauth_access_token_data)

    def log_out(self) -> None:
        self._clear_credentials()
        self._clear_token_profile()

    def get_site_and_firmware_data(self, **kwargs) -> None:
        """Get the available sites and firmware images."""
        data = {
            "query": """
            {
                allFirmwareImages {
                    edges { node {
                        id, name, version, bootloader { id }, file, hashSha3_512
                    } }
                }
                allBootloaderImages {
                    edges { node {
                        id, name, version, file, hashSha3_512
                    } }
                }
                allSites {
                    edges { node {
                        id, name
                    } }
                }
                allControllerTypes(isGlobal: true, name: "ESP32") {
                    edges { node {
                        id, name, isGlobal
                    } }
                }
            }""",
            "variables": None,
        }
        output = self._auth_server_request(self._graphql_url, data).json()
        if errors := output.get("errors"):
            logging.warning(errors)
            raise WorkerWarning("Error while getting site and firmware data.")

        # Store firmware image metadata. Sort them by their semantic version
        firmware_images = [
            i["node"] for i in output["data"]["allFirmwareImages"]["edges"]
        ]
        firmware_images = [i for i in firmware_images if i["version"] != "-1"]
        firmware_images.sort(key=lambda x: Version(x["version"]), reverse=True)
        self._config.config["firmwareImages"] = firmware_images

        # Store bootload image metadata. Sort them by their semantic version
        bootloader_images = [
            i["node"] for i in output["data"]["allBootloaderImages"]["edges"]
        ]
        bootloader_images.sort(key=lambda x: Version(x["version"]), reverse=True)
        self._config.config["bootloaderImages"] = bootloader_images

        # Store sites and controller types
        sites = self.parse_sites(output["data"]["allSites"]["edges"])
        self._config.cache_sites(sites)

        controller_types = [
            i["node"] for i in output["data"]["allControllerTypes"]["edges"]
        ]
        self._config.config["controllerTypes"] = controller_types

    def get_controller_data(self, site_id: str, **kwargs) -> List[ControllerModel]:
        """Get the available controllers for a given site."""
        data = {
            "query": f"""
            {{
                allControllers(site: "{site_id}") {{
                    pageInfo {{ hasNextPage }}
                    edges {{ node {{
                        id, name, authToken {{ key }}, controllerTypeId
                        partitionTableId, firmwareImageId, siteId
                    }} }}
                }}
            }}
            """,
            "variables": None,
        }
        output = self._auth_server_request(self._graphql_url, data).json()
        if errors := output.get("errors"):
            logging.warning(errors)
            raise WorkerWarning("Error while getting controller data.")
        results = output["data"]["allControllers"]
        if results["pageInfo"]["hasNextPage"]:
            message = (
                "Not all controllers for this site could be fetched. Please upgrade your Inamata"
                "Flasher tool."
            )
            raise WorkerInformation(message)
        if "edges" not in results:
            return None
        controllers = self.parse_controllers(results["edges"])
        self._config.cache_controllers(controllers)
        return controllers

    def get_default_partition_table(self) -> dict:
        """Try to get the default partition table."""
        if partition_table := self._get_cached_partition_table(
            self._default_partition_table_id
        ):
            return partition_table

        # Search for the partition table from the server
        partition_table_name = self._default_partition_table_name
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
        output = self._auth_server_request(self._graphql_url, data).json()
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
        self._default_partition_table_id = partition_table_id
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
        output = self._auth_server_request(self._graphql_url, data).json()
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
    ) -> ControllerModel:
        """Create and register a controller on the server."""
        partition_table = self.get_default_partition_table()
        data = {
            "query": """
            mutation createController($input: CreateControllerInput!) {
                createController(input: $input) {
                    controller {
                        id, name, authToken { key }, controllerTypeId
                        partitionTableId, firmwareImageId, siteId
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
        output = self._auth_server_request(self._graphql_url, data).json()
        if errors := output.get("errors"):
            logging.warning(errors[0]["message"])
            raise WorkerWarning(errors[0]["message"])
        controller_data = output["data"]["createController"]["controller"]
        controller = self.parse_controller(controller_data)
        self._config.cache_controllers([controller])
        return controller

    def update_controller(
        self, controller: ControllerModel, **kwargs
    ) -> ControllerModel:
        """Update a controller."""
        data = {
            "query": """
            mutation updateController($input: UpdateControllerInput!) {
                updateController(input: $input) { success }
            }
            """,
            "variables": json.dumps(
                {
                    "input": {
                        "name": controller.name,
                        "site": controller.site_id,
                        "controller": controller.id,
                        "controllerType": controller.controller_type_id,
                        "partitionTable": controller.partition_table_id,
                        "firmwareImage": controller.firmware_image_id,
                    }
                }
            ),
        }
        output = self._auth_server_request(self._graphql_url, data).json()
        if errors := output.get("errors"):
            logging.warning(errors[0]["message"])
            raise WorkerWarning(errors[0]["message"])
        self._config.cache_controllers([controller])
        return controller

    def cycle_controller_auth_token(
        self, controller_id: str, **kwargs
    ) -> ControllerModel:
        """Cycle a controller's auth token to prevent duplicate connections."""
        data = {
            "query": """
            mutation cycleControllerAuthToken($input: CycleControllerAuthTokenInput!) {
                cycleControllerAuthToken(input: $input) {
                    controllerAuthToken { key }
                }
            }
            """,
            "variables": json.dumps({"input": {"controller": controller_id}}),
        }
        output = self._auth_server_request(self._graphql_url, data).json()
        if errors := output.get("errors"):
            logging.warning(errors[0]["message"])
            raise WorkerWarning(errors[0]["message"])
        controller = self._config.get_controller(controller_id)
        if not controller:
            raise WorkerInformation(
                "Could not find the controller. Please reload the controller data."
            )
        key = output["data"]["cycleControllerAuthToken"]["controllerAuthToken"]["key"]
        controller.auth_token = key
        self._config.cache_controllers([controller])
        return controller

    def get_username(self) -> str:
        return self._config.config.get("username", "")

    def try_access_token_refresh(self, **kwargs) -> bool:
        """Returns true if authenticated.

        Raises:
            WorkerError: On network error
        """
        try:
            success = self._refresh_access_token()
        except WorkerError as err:
            raise WorkerWarning(
                "Failed connecting to the server. Check your internet connection or contact Inamata."
            ) from err
        return success

    def download_firmware_image(self, firmware_id: str, **kwargs) -> dict:
        """Download the selected firmware if it is not cached locally."""
        try:
            firmwares = self._config.config["firmwareImages"]
            firmware = next(i for i in firmwares if i["id"] == firmware_id)
            firmware = self._download_image(
                firmware,
                self._refresh_firmware_image_url,
                kwargs.get("progress_callback", None),
            )
        except KeyError as err:
            message = (
                f"Error downloading firmware. Not all required metadata found ({err})."
            )
            raise WorkerWarning(message)
        return firmware

    def get_firmware_image(self, firmware_image_id: str) -> dict:
        """Returns the firmware image for a given ID."""
        firmware_image = next(
            i
            for i in self._config.config.get("firmwareImages")
            if i["id"] == firmware_image_id
        )
        return firmware_image

    def download_bootloader_image(self, bootloader_id: str, **kwargs) -> dict:
        """Download the selected bootloader if it is not cached locally."""
        try:
            bootloaders = self._config.config["bootloaderImages"]
            bootloader = next(i for i in bootloaders if i["id"] == bootloader_id)
            bootloader = self._download_image(
                bootloader,
                self._refresh_bootloader_image_url,
                kwargs.get("progress_callback", None),
            )
        except KeyError as err:
            message = f"Error downloading bootloader. Not all required metadata found ({err})."
            raise WorkerWarning(message)
        return bootloader

    def get_bootloader_image(self, bootloader_image_id: str) -> dict:
        """Returns the bootloader image for a given ID."""
        bootloader_image = next(
            i
            for i in self._config.config.get("bootloaderImages")
            if i["id"] == bootloader_image_id
        )
        return bootloader_image

    def get_image_path(self, image: dict) -> str:
        """Returns the absolute path to the image."""
        parse_result = urlparse(image["file"])
        filename = os.path.basename(parse_result.path)
        return os.path.join(self._config.dirs.user_cache_dir, filename)

    def _download_image(
        self,
        image: dict,
        refresh_url: Callable[[dict], None],
        progress_callback: Optional[Callable[[int], None]],
    ) -> dict:
        """Download the selected image if it is not locally cached."""
        path = self.get_image_path(image)
        # If the file has been downloaded to the cache and has the same hash, return
        if self._is_file_valid(path, image["hashSha3_512"]):
            return image
        # Download the file and notify of progress
        os.makedirs(self._config.dirs.user_cache_dir, exist_ok=True)
        with open(path, "wb+") as f:
            # If the download link has expired, request a new one and retry
            response = requests.get(image["file"], stream=True)
            if response.status_code >= 400:
                refresh_url(image)
                response = requests.get(image["file"], stream=True)
                if response.status_code >= 400:
                    logging.error(
                        f"Failed to download file (Error {response.status_code})"
                    )
                    raise WorkerWarning(
                        "Failed downloading the file. Try refreshing, check your internet connection or contact support."
                    )
            total_length = response.headers.get("content-length")
            # If the total length is unknown, skip notifying progress
            if total_length is None:
                if progress_callback:
                    progress_callback(-1)
                f.write(response.content)
            else:
                received_bytes = 0
                total_length = int(total_length)
                for data in response.iter_content(chunk_size=64 * 1024):
                    f.write(data)
                    received_bytes += len(data)
                    percentage_done = int(100 * received_bytes / total_length)
                    if progress_callback:
                        progress_callback.emit(percentage_done)
        # Check the file hash. Delete and inform the user if it fails
        if not self._is_file_valid(path, image["hashSha3_512"]):
            os.remove(path)
            raise WorkerWarning(
                "Checksum of downloaded file did not match. Please try another"
                " version or contact support."
            )
        return image

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

    def _refresh_firmware_image_url(self, firmware_image: dict):
        """Refresh the (expired) URL of a firmware image."""
        data = {
            "query": f"""
            {{
                firmwareImage(id: "{firmware_image['id']}") {{ file }}
            }}""",
            "variables": None,
        }
        output = self._auth_server_request(self._graphql_url, data).json()
        if errors := output.get("errors"):
            logging.warning(errors)
            raise WorkerWarning(
                "Error while refreshing the firmware URL. Please reload data."
            )
        firmware_image["file"] = output["data"]["firmwareImage"]["file"]

    def _refresh_bootloader_image_url(self, bootloader_image):
        """Refresh the (expired) URL of a bootloader image."""
        data = {
            "query": f"""
            {{
                bootloaderImage(id: "{bootloader_image['id']}") {{ file }}
            }}"""
        }
        output = self._auth_server_request(self._graphql_url, data).json()
        if errors := output.get("errors"):
            logging.warning(errors)
            raise WorkerWarning(
                "Error while refreshing the bootloader URL. Please reload data."
            )
        bootloader_image["file"] = output["data"]["bootloaderImage"]["file"]

    def _save_credentials(self, access_token: str, refresh_token: str) -> None:
        """Save the auth token in a keychain."""

        # Cache the tokens and their decoded data, to be access via propery functions
        self._oauth_access_token_cache = access_token
        self._oauth_access_token_data_cache = self._decode_access_token(access_token)
        self._oauth_refresh_token_cache = refresh_token
        self._oauth_refresh_token_data_cache = self._decode_refresh_token(refresh_token)

        # Store the refresh token for future application starts
        username = self._oauth_access_token_data["preferred_username"]
        self._config.config["username"] = username
        try:
            keyring.set_password(self._config.app_name, username, refresh_token)
        except KeyringError as err:
            # If the system keyring is broken, do not restrict remaining functionality
            logging.warn("Failed to store refresh token in system keyring")

    def _clear_credentials(self) -> None:
        """Clear the username and auth token"""
        self._oauth_access_token_cache = ""
        self._oauth_access_token_data_cache = {}
        self._oauth_refresh_token_cache = ""
        self._oauth_refresh_token_data_cache = {}
        if username := self._config.config.get("username"):
            try:
                keyring.delete_password(self._config.app_name, username)
            except PasswordDeleteError:
                pass

    def _auth_server_request(self, url, data, headers=None):
        """Make a GraphQL server request with the cached auth token."""
        if not headers:
            headers = {**self._default_headers}
        if self._is_token_expired(self._oauth_access_token_data):
            updated = self._refresh_access_token()
            if not updated:
                raise WorkerWarning("Access has expired. Please log in again.")
        headers = {**headers, "Authorization": f"Token {self._oauth_access_token}"}
        return self._server_request(url, data, headers)

    def _server_request(
        self,
        url: str,
        data: Dict[str, str],
        headers: Optional[Dict[str, str]] = None,
        raise_for_status: Optional[bool] = True,
    ) -> requests.Response:
        """Make a GraphQL server request that handles HTTP errors."""
        if not headers:
            headers = self._default_headers
        try:
            response = requests.post(url, data, headers=headers, timeout=10)
            if raise_for_status:
                response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            if err.response.status_code == 400 and err.request.url == self._graphql_url:
                logging.warning(f"GraphQL error: {err.response.content}")
                message = (
                    "An error occured while requesting data from the server API."
                    " Check that you're using an up-to-date version of the Inamata Flasher tool"
                )
                raise WorkerWarning(message) from err
            raise WorkerWarning(str(err)) from err
        except requests.exceptions.ConnectionError as err:
            error_type = type(err.args[0]).__name__
            message = f"Failed connecting to server: {error_type}"
            raise WorkerWarning(message) from err
        except requests.exceptions.Timeout as err:
            raise WorkerWarning(str(err)) from err
        except requests.exceptions.RequestException as err:
            raise WorkerWarning(str(err)) from err
        return response

    def _decode_refresh_token(self, token, raise_error: bool = False) -> Optional[Dict]:
        try:
            data = jwt.decode(token, options={"verify_signature": False})
        except jwt.InvalidTokenError as err:
            if raise_error:
                raise err
            return None
        return data

    def _decode_access_token(self, token, raise_error: bool = False) -> Optional[Dict]:
        """
        Attempts to decode the token. Returns a Dict on success or none on failure
        """
        # Get the public key from the identity provider, i.e., the keycloak server
        public_key = self._jwks_client.get_signing_key_from_jwt(token).key
        # Decode and verify the JWT with the server's public key specified in the
        # JWT's header, the required audience and the allowed crypto algorithms it
        # published
        try:
            data = jwt.decode(
                token,
                public_key,
                audience=self._access_token_audience,
                algorithms=self._openid_config["id_token_signing_alg_values_supported"],
            )
        except jwt.InvalidTokenError as err:
            if raise_error:
                raise err
            return None
        return data

    def _store_token_profile(self, token_data: Dict) -> None:
        """Extract all profile entries specified in the openid profile keys.

        If the keys are not present in the token, they will be removed from the local
        config to remove stale data.
        """
        for key in self._openid_profile_keys:
            if value := token_data.get(key):
                self._config.config[key] = value
            else:
                self._config.config.pop(key, None)

    def _clear_token_profile(self) -> None:
        """Clear the set profile entries loaded from an access token."""
        for key in self._openid_profile_keys:
            self._config.config.pop(key, None)

    def _refresh_access_token(self) -> bool:
        """Try to get a new access token with the refresh token.

        Returns true if the update was successful."""
        logging.debug("Refreshing the access token")
        headers = {"content-type": "application/x-www-form-urlencoded"}
        data = {
            "client_id": self._oauth_client_id,
            "grant_type": "refresh_token",
            "refresh_token": self._oauth_refresh_token,
        }
        response = self._server_request(
            self._oauth_token_url, data, headers=headers, raise_for_status=False
        )
        if not response.ok:
            logging.warn("Failed to refresh access token")
            return False
        tokens = response.json()
        self._save_credentials(tokens["access_token"], tokens["refresh_token"])
        self._store_token_profile(self._oauth_access_token_data)
        logging.info("Successfully refreshed the access token")
        return True

    def _load_stored_refresh_token(self) -> bool:
        username = self._config.config.get("username")
        if not username:
            return False
        try:
            credential = keyring.get_credential(self._config.app_name, username)
        except KeyringError as err:
            return False
        if not credential:
            return False
        refresh_token = credential.password
        data = self._decode_refresh_token(refresh_token)
        self._oauth_refresh_token_cache = refresh_token
        self._oauth_refresh_token_data_cache = data
        return True

    @staticmethod
    def _is_token_expired(
        token_data: Dict, buffer: Optional[timedelta] = timedelta(seconds=60)
    ):
        """Returns true if the token has expired or invalid with a buffer of 60s."""
        try:
            expiration = datetime.fromtimestamp(token_data.get("exp"), tz=timezone.utc)
        except TypeError:
            return True
        # If the expiration date lies in the future, it is valid
        if expiration > datetime.now(tz=timezone.utc):
            return False
        return True

    @property
    def _oauth_refresh_token(self) -> str:
        """Return the refresh token or an empty string."""
        # If it is cached, return it from there, else use the system keyring
        if not self._oauth_refresh_token_cache:
            self._load_stored_refresh_token()
        return self._oauth_refresh_token_cache

    @property
    def _oauth_refresh_token_data(self) -> Dict:
        """Return the decoded refresh token or an empty dict."""
        if not self._oauth_refresh_token_data_cache:
            self._load_stored_refresh_token()
        return self._oauth_refresh_token_data_cache

    @property
    def _oauth_access_token(self) -> str:
        return self._oauth_access_token_cache

    @property
    def _oauth_access_token_data(self) -> Dict:
        return self._oauth_access_token_data_cache

    @property
    def _oauth_device_url(self) -> str:
        return f"{self._oauth_base_url}{self._oauth_device_path}"

    @property
    def _oauth_token_url(self) -> str:
        return f"{self._oauth_base_url}{self._oauth_token_path}"

    @cached_property
    def _openid_config(self) -> Dict[str, str]:
        url = f"{self._oauth_base_url}{self._openid_config_path}"
        return requests.get(url, self._default_headers).json()

    @cached_property
    def _jwks_client(self):
        """Collects the identity provider's public keys"""
        return jwt.PyJWKClient(self._openid_config["jwks_uri"])

    @property
    def _graphql_url(self) -> str:
        return f"{self._core_base_url}{self._core_graphql_path}"

    @property
    def _default_headers(self) -> Dict[str, str]:
        parsed_core_url = urlparse(self._core_base_url)
        return {"Host": parsed_core_url.netloc}

    @staticmethod
    def parse_sites(data: List) -> List[SiteModel]:
        """Expects data as [{"node: {...}, ...]"""
        return [SiteModel(id=i["node"]["id"], name=i["node"]["name"]) for i in data]

    @classmethod
    def parse_controllers(cls, data: List) -> List[ControllerModel]:
        """Expects data as [{"node": {...}}, ...]}"""
        return [cls.parse_controller(i["node"]) for i in data]

    @staticmethod
    def parse_controller(data: Dict) -> ControllerModel:
        """Expects data as {"id: ..., "name": ...}"""
        return ControllerModel(
            id=data["id"],
            name=data["name"],
            site_id=data["siteId"],
            controller_type_id=data["controllerTypeId"],
            firmware_image_id=data["firmwareImageId"],
            partition_table_id=data["partitionTableId"],
            auth_token=data["authToken"]["key"] if data["authToken"] else None,
        )
