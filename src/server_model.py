import base64
import dataclasses
import hashlib
import logging
import os
import uuid
import webbrowser
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from functools import cached_property
from time import sleep
from typing import Callable, Dict, List, Optional
from urllib.parse import urlparse

import jwt
import keyring
import requests
from keyring.errors import KeyringError, PasswordDeleteError
from PySide6.QtCore import QCoreApplication
from semantic_version import Version

try:
    from jeepney.wrappers import DBusErrorResponse
except ImportError:

    class DBusErrorResponse(Exception):
        pass


from config import (
    BootloaderImageModel,
    Config,
    ControllerModel,
    ControllerTypeModel,
    FirmwareImageModel,
    FirmwareVariantEdge,
    FirmwareVariantModel,
    SiteModel,
)
from worker import WorkerError, WorkerInformation, WorkerWarning

SNAP_PASSWORD_MANAGER_SERVICE_ERROR = "Snap not connected to password-manager-service. Run: snap connect inamata-flasher:password-manager-service"


class WebAppPaths:
    """Collection of web-app paths"""

    devices_peripherals = "devices/peripherals"
    devices_controllers = "devices/controllers"
    devices_data_points = "devices/data-points"

    tasks_overview = "tasks/overview"
    tasks_logging = "tasks/logging"

    cp_overview = "plans/overview"
    cp_editor = "plans/editor"
    cp_monitor = "plans/monitor"

    dashboards_overview = "dashboards/overview"
    dashboards_graphs = "dashboards/graphs"


class ServerModel:
    """Used to login to the Inamata server."""

    @dataclass
    class ServerUrls:
        core_base_url: str
        oauth_base_url: str
        web_app_base_url: str

    _core_graphql_path = "/graphql/"

    _oauth_client_id = "flasher"
    _oauth_realm = "inamata"
    _oauth_sign_up_path = (
        f"/realms/{_oauth_realm}/protocol/openid-connect/registrations"
    )
    _oauth_device_path = f"/realms/{_oauth_realm}/protocol/openid-connect/auth/device"
    _oauth_token_path = f"/realms/{_oauth_realm}/protocol/openid-connect/token"
    _openid_config_path = f"/realms/{_oauth_realm}/.well-known/openid-configuration"
    _openid_profile_keys = ["name", "email", "given_name", "family_name"]
    _access_token_audience = ["core-service", "account"]
    _keyring_disabled = False

    _github_latest_url = (
        "https://api.github.com/repos/inamataio/flasher/releases/latest"
    )
    github_linux_download_url = "https://github.com/InamataIO/Flasher/releases/latest/download/inamata_flasher-linux-x86_64"
    github_windows_download_url = "https://github.com/InamataIO/Flasher/releases/latest/download/inamata_flasher_setup.exe"
    github_latest_release_url = "https://github.com/InamataIO/Flasher/releases/latest"

    @property
    def _refresh_token_audience(self) -> str:
        return f"{self.server_urls.oauth_base_url}/realms/{self._oauth_realm}"

    _default_partition_table_name = "min_spiffs"
    _default_partition_table_id = ""

    _known_servers = {
        "staging": ServerUrls(
            core_base_url="https://core.staging.inamata.io",
            oauth_base_url="https://auth.staging.inamata.io",
            web_app_base_url="https://app.staging.inamata.io",
        ),
        "production": ServerUrls(
            core_base_url="https://core.inamata.io",
            oauth_base_url="https://auth.inamata.io",
            web_app_base_url="https://app.inamata.io",
        ),
    }

    @property
    def core_domain(self) -> str:
        return urlparse(self.server_urls.core_base_url).hostname

    @property
    def is_core_url_secure(self) -> str:
        return urlparse(self.server_urls.core_base_url).scheme == "https"

    def __init__(self, config: Config):
        self._config: Config = config
        self._oauth_access_token_cache: str = ""
        self._oauth_access_token_data_cache: Dict = {}
        self._oauth_refresh_token_cache: str = ""
        self._oauth_refresh_token_data_cache: Dict = {}
        self._server_name: str = self.default_server
        self._load_server_config()
        self._github_latest_version = ""

    @property
    def default_server(self) -> str:
        return "production"

    @property
    def default_dev_server_urls(self) -> ServerUrls:
        return self.ServerUrls(
            core_base_url="http://localhost:8000",
            oauth_base_url="http://localhost:8080",
            web_app_base_url="http://localhost:4200",
        )

    @property
    def server_name(self) -> str:
        return self._server_name

    @property
    def known_server_urls(self) -> dict[str, ServerUrls]:
        return self._known_servers

    @property
    def server_urls(self) -> ServerUrls:
        return self._known_servers[self._server_name]

    @server_urls.setter
    def server_urls(self, value: str | ServerUrls) -> None:
        """If server urls change, clear token and cached credentials."""
        match value:
            case str():
                self._server_name = value
            case self.ServerUrls():
                self._server_name = self.dev_server_name
                self._known_servers[self.dev_server_name] = value
            case _ as variable_type:
                logging.error(f"Unknown type: {variable_type}")
                return
        self.log_out()

    @property
    def dev_server_urls(self) -> ServerUrls:
        return dataclasses.replace(self._known_servers[self.dev_server_name])

    @property
    def dev_server_name(self) -> str:
        return "dev"

    @property
    def sign_up_url(self) -> str:
        return (
            f"{self.server_urls.oauth_base_url}{self._oauth_sign_up_path}"
            "?client_id=web-app&response_type=code"
            f"&redirect_uri={self.server_urls.web_app_base_url}"
        )

    @property
    def github_latest_version(self) -> str:
        return self._github_latest_version

    def restore_dev_server_urls(self) -> None:
        self._known_servers["dev"] = self.default_dev_server_urls

    def save_to_config(self) -> None:
        """Save server URLs to config if not the default."""
        server_config = {"server_name": self.server_name}
        if self._known_servers["dev"] != self.default_dev_server_urls:
            server_config["dev_urls"] = {
                "core_base_url": self._known_servers["dev"].core_base_url,
                "oauth_base_url": self._known_servers["dev"].oauth_base_url,
                "web_app_base_url": self._known_servers["dev"].web_app_base_url,
            }
        self._config.config["server"] = server_config

    def _load_server_config(self) -> None:
        """Load server URLs from config."""
        server_config = self._config.config.get("server", {})
        if server_name := server_config.get("server_name"):
            self._server_name = server_name
        if dev_urls := server_config.get("dev_urls"):
            self._known_servers["dev"] = self.ServerUrls(
                core_base_url=dev_urls.get("core_base_url", ""),
                oauth_base_url=dev_urls.get("oauth_base_url", ""),
                web_app_base_url=dev_urls.get("web_app_base_url", ""),
            )
        else:
            self.restore_dev_server_urls()

    def log_in(self, **kwargs) -> None:
        """Log in to the Inamata server and get an auth token."""

        data = {"client_id": self._oauth_client_id, "scope": "offline_access"}
        headers = {
            "content-type": "application/x-www-form-urlencoded",
        }
        response = self._server_request(self._oauth_device_url, data, headers=headers)
        device_auth = response.json()
        state_callback = kwargs.get("state_callback", None)
        if state_callback:
            state_callback.emit(device_auth["verification_uri_complete"])
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

    def get_static_data(self, controller_type_names: list[str], **kwargs) -> None:
        """Get the available sites, controller types and bootload images."""
        data = {
            "query": """
            query staticData($controllerTypes: [String!]) {
                allSites {
                    edges { node {
                        id, name
                    } }
                }
                allControllerTypes(filters: {isGlobal: true, name: {inList: $controllerTypes}}) {
                    edges { node {
                        id, name, firmwareVariantEdges { edges { node {
                            priority, firmwareVariant { id, name }
                        } } }
                    } }
                }
                allBootloaderImages {
                    edges { node {
                        id, name, version, hashSha3_512
                    } }
                }
            }""",
            "variables": {"controllerTypes": controller_type_names},
        }
        output = self._auth_server_request(self._graphql_url, data).json()
        if errors := output.get("errors"):
            logging.warning(errors)
            raise WorkerWarning(self.getting_site_controller_type_error)

        # Cache sites, controller types, firmware variants and bootloaders
        sites = self.parse_sites(output)
        self._config.cache_sites(sites)
        controller_types, firmware_variants = self.parse_controller_type_data(output)
        self._config.cache_controller_types(controller_types)
        self._config.cache_firmware_variants(firmware_variants)
        bootloader_images = self.parse_bootloader_images(output)
        self._config.cache_bootloader_images(bootloader_images)

    def get_firmware_data(self, firmware_variant_id: str, **kwargs) -> None:
        """Get the available firmware images for a controller type."""
        data = {
            "query": """
            query firmwareData($firmwareVariantId: GlobalID!) {
                allFirmwareImages(
                    filters: {firmwareVariant: {id: $firmwareVariantId} }
                    order: {createdAt: DESC}
                ) { edges { node {
                    id, name, version, bootloaderId, hashSha3_512
                } } }
            }""",
            "variables": {"firmwareVariantId": firmware_variant_id},
        }
        output = self._auth_server_request(self._graphql_url, data).json()
        if errors := output.get("errors"):
            logging.warning(errors)
            raise WorkerWarning(self.getting_site_firmware_error)

        # Store firmware image metadata. Sort them by their semantic version
        firmware_images = self.parse_firmware_images(output, firmware_variant_id)
        self._config.cache_firmware_images(firmware_images)
        self._config.cache_firmware_images_in_variant(
            firmware_variant_id, firmware_images.keys()
        )

    def get_controller_data(self, site_id: str, **kwargs) -> List[ControllerModel]:
        """Get the available controllers for a given site."""
        data = {
            "query": """
            query controllerData($siteId: GlobalID!) {
                allControllers(filters: {site: {id: $siteId } }) {
                    pageInfo { hasNextPage }
                    edges { node {
                        id, name, controllerTypeId, partitionTableId, siteId
                        firmwareImage {
                            id, name, version, hashSha3_512, bootloaderId, firmwareVariantId
                        }
                    } }
                }
            }""",
            "variables": {"siteId": site_id},
        }
        output = self._auth_server_request(self._graphql_url, data).json()
        if errors := output.get("errors"):
            logging.warning(errors)
            raise WorkerWarning(self.getting_controller_error)
        results = output["data"]["allControllers"]
        if results["pageInfo"]["hasNextPage"]:
            raise WorkerInformation(self.too_many_controllers_error)
        if "edges" not in results:
            return []
        controllers = self.parse_controllers(results["edges"])
        self._config.cache_controllers(controllers)
        firmware_images = self.parse_controllers_firmware_image(results["edges"])
        self._config.cache_firmware_images(firmware_images)
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
                    filters: {{ isGlobal: true, name: {{exact: "{partition_table_name}"}} }},
                    first: 1
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
            raise WorkerWarning(self.getting_default_partition_table_error)
        results = output["data"]["allControllerPartitionTables"]["edges"]
        partition_tables = [i["node"] for i in results]
        if not partition_tables:
            raise WorkerWarning(
                f"{self.default_partition_table_not_found_error} ({partition_table_name})"
            )
        partition_table_id = partition_tables[0]["id"]
        self._default_partition_table_id = partition_table_id
        self._cache_partition_table(partition_table_id, partition_tables[0])
        return partition_tables[0]

    def get_partition_table(self, partition_table_id: str) -> dict:
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
            raise WorkerWarning(self.getting_partition_table_error)
        partition_table = output["data"]["controllerPartitionTable"]
        # Check if the partition table was found on the server
        if not partition_table:
            raise WorkerWarning(self.partition_table_not_found_error)
        self._cache_partition_table(partition_table_id, partition_table)
        return partition_table

    def register_controller(
        self, name, site_id, controller_type_id, firmware_image_id, **kwargs
    ) -> ControllerModel:
        """Create and register a controller on the server."""
        partition_table = self.get_default_partition_table()
        controller_id = base64.b64encode(
            f"ControllerGQLNode:{uuid.uuid4()}".encode()
        ).decode()
        data = {
            "query": """
            mutation createController($input: CreateControllerInput!) {
                createController(input: $input) {
                    ... on ControllerGQLNode {
                        id, name, authToken { key }, controllerTypeId
                        partitionTableId, firmwareImageId, siteId
                    }
                }
            }
            """,
            "variables": {
                "input": {
                    "name": name,
                    "controllerId": controller_id,
                    "siteId": site_id,
                    "controllerTypeId": controller_type_id,
                    "partitionTableId": partition_table["id"],
                    "firmwareImageId": firmware_image_id,
                }
            },
        }
        output = self._auth_server_request(self._graphql_url, data).json()
        if errors := output.get("errors"):
            logging.warning(errors[0]["message"])
            raise WorkerWarning(errors[0]["message"])
        controller_data = output["data"]["createController"]
        controller = self.parse_controller(controller_data)
        self._config.cache_controllers({controller.id: controller})
        return controller

    def update_controller(
        self, controller: ControllerModel, **kwargs
    ) -> ControllerModel:
        """Update a controller."""
        data = {
            "query": """
            mutation updateController($input: UpdateControllerInput!) {
                updateController(input: $input) { ... on Success { success } }
            }
            """,
            "variables": {
                "input": {
                    "controllerId": controller.id,
                    "name": controller.name,
                    "controllerTypeId": controller.controller_type_id,
                    "partitionTableId": controller.partition_table_id,
                    "firmwareImageId": controller.firmware_image_id,
                }
            },
        }
        output = self._auth_server_request(self._graphql_url, data).json()
        if errors := output.get("errors"):
            logging.warning(errors[0]["message"])
            raise WorkerWarning(errors[0]["message"])
        self._config.cache_controllers({controller.id: controller})
        return controller

    def cycle_controller_auth_token(
        self, controller_id: str, **kwargs
    ) -> ControllerModel:
        """Cycle a controller's auth token to prevent duplicate connections."""
        data = {
            "query": """
            mutation cycleControllerAuthToken($input: CycleControllerAuthTokenInput!) {
                cycleControllerAuthToken(input: $input) {
                    ... on ControllerAuthTokenGQLNode { key }
                }
            }
            """,
            "variables": {"input": {"controllerId": controller_id}},
        }
        output = self._auth_server_request(self._graphql_url, data).json()
        if errors := output.get("errors"):
            logging.warning(errors[0]["message"])
            raise WorkerWarning(errors[0]["message"])
        controller = self._config.get_controller(controller_id)
        if not controller:
            raise WorkerInformation(self.controller_not_found_error)
        key = output["data"]["cycleControllerAuthToken"]["key"]
        controller.auth_token = key
        self._config.cache_controllers({controller.id: controller})
        return controller

    def delete_controller(self, controller_id: str, **kwargs) -> None:
        """Delete a controller."""
        data = {
            "query": """
            mutation deleteController($input: DeleteControllerInput!) {
                deleteController(input: $input) { ... on Success { success } }
            }
            """,
            "variables": {"input": {"controllerId": controller_id}},
        }
        output = self._auth_server_request(self._graphql_url, data).json()
        if errors := output.get("errors"):
            logging.warning(errors[0]["message"])
            raise WorkerWarning(errors[0]["message"])
        success = output["data"]["deleteController"]["success"]
        if not success:
            logging.warning(f"Failed deleting controller: {controller_id}")
            raise WorkerWarning(self.deleting_controller_error)

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
            raise WorkerWarning(self.auth_server_error) from err
        return success

    def download_firmware_image(self, firmware_id: str, **kwargs) -> dict:
        """Download the selected firmware if it is not cached locally."""
        try:
            firmware = self._config.get_firmware_image(firmware_id)
            firmware = self._download_image(
                firmware,
                self._refresh_firmware_image_url,
                kwargs.get("progress_callback", None),
            )
        except KeyError as err:
            message = f"{self.downloading_firmware_error} {err}"
            raise WorkerWarning(message)
        return firmware

    def download_bootloader_image(self, bootloader_id: str, **kwargs) -> dict:
        """Download the selected bootloader if it is not cached locally."""
        try:
            bootloader = self._config.get_bootloader_image(bootloader_id)
            bootloader = self._download_image(
                bootloader,
                self._refresh_bootloader_image_url,
                kwargs.get("progress_callback", None),
            )
        except KeyError as err:
            raise WorkerWarning(f"{self.downloading_bootloader_error} {err}")
        return bootloader

    def get_image_path(self, image: FirmwareImageModel) -> str:
        """Returns the absolute path to the image."""
        if not image.file:
            return ""
        parse_result = urlparse(image.file)
        filename = os.path.basename(parse_result.path)
        return os.path.join(self._config.dirs.user_cache_dir, filename)

    def update_newest_version(self, **kwargs) -> str:
        """Returns the version of the newest release."""
        response = requests.get(self._github_latest_url)
        if response.status_code >= 400:
            return ""
        release_data = response.json()
        version_tag = release_data.get("tag_name", "")
        if not version_tag:
            return ""
        version = version_tag[1:] if version_tag[0] == "v" else version_tag
        self._github_latest_version = version
        return version

    def _download_image(
        self,
        image: FirmwareImageModel,
        refresh_url: Callable[[dict], None],
        progress_callback: Optional[Callable[[int], None]],
    ) -> dict:
        """Download the selected image if it is not locally cached."""
        if not image.file:
            refresh_url(image)
        path = self.get_image_path(image)
        # If the file has been downloaded to the cache and has the same hash, return
        if self._is_file_valid(path, image.hash_sha3_512):
            return image
        # Download the file and notify of progress
        os.makedirs(self._config.dirs.user_cache_dir, exist_ok=True)
        # If the download link has expired, request a new one and retry
        response = requests.get(image.file, stream=True)
        if response.status_code >= 400:
            refresh_url(image)
            response = requests.get(image.file, stream=True)
            if response.status_code >= 400:
                logging.error(f"Failed to download file (Error {response.status_code})")
                raise WorkerWarning(self.download_failed_error)
        total_length = response.headers.get("content-length")
        # If the total length is unknown, skip notifying progress
        with open(path, "wb+") as file:
            if total_length is None:
                if progress_callback:
                    progress_callback(-1)
                file.write(response.content)
            else:
                received_bytes = 0
                total_length = int(total_length)
                for data in response.iter_content(chunk_size=64 * 1024):
                    file.write(data)
                    received_bytes += len(data)
                    percentage_done = int(100 * received_bytes / total_length)
                    if progress_callback:
                        progress_callback.emit(percentage_done)
        # Check the file hash. Delete and inform the user if it fails
        if not self._is_file_valid(path, image.hash_sha3_512):
            os.remove(path)
            raise WorkerWarning(self.checksum_failed_error)
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

    def _get_cached_partition_table(self, partition_table_id: str) -> dict:
        """Try to get the cached partition table. Empty dict on cache miss."""
        try:
            partition_table = self._config._cache["partitionTables"][partition_table_id]
            return partition_table
        except KeyError:
            return {}

    def _cache_partition_table(self, partition_table_id, partition_table) -> None:
        """Store the partition table in the cache."""
        try:
            partition_tables = self._config._cache["partitionTables"]
        except KeyError:
            partition_tables = {}
        partition_tables.update({partition_table_id: partition_table})

    def _refresh_firmware_image_url(self, firmware_image: FirmwareImageModel):
        """Refresh the (expired) URL of a firmware image."""
        data = {
            "query": f"""
            {{
                firmwareImage(id: "{firmware_image.id}") {{ file }}
            }}""",
            "variables": None,
        }
        output = self._auth_server_request(self._graphql_url, data).json()
        if errors := output.get("errors"):
            logging.warning(errors)
            raise WorkerWarning(self.refreshing_firmware_url_failed_error)
        firmware_image.file = output["data"]["firmwareImage"]["file"]

    def _refresh_bootloader_image_url(self, bootloader_image: BootloaderImageModel):
        """Refresh the (expired) URL of a bootloader image."""
        data = {
            "query": f"""
            {{
                bootloaderImage(id: "{bootloader_image.id}") {{ file }}
            }}"""
        }
        output = self._auth_server_request(self._graphql_url, data).json()
        if errors := output.get("errors"):
            logging.warning(errors)
            raise WorkerWarning(self.refreshing_bootloader_url_failed_error)
        bootloader_image.file = output["data"]["bootloaderImage"]["file"]

    def _save_credentials(self, access_token: str, refresh_token: str) -> None:
        """Save the auth token in a keychain."""

        # Cache the tokens and their decoded data, to be access via propery functions
        self._oauth_access_token_cache = access_token
        self._oauth_access_token_data_cache = self._decode_access_token(
            access_token, True
        )
        self._oauth_refresh_token_cache = refresh_token
        self._oauth_refresh_token_data_cache = self._decode_refresh_token(
            refresh_token, True
        )

        # Store the refresh token for future application starts
        username = self._oauth_access_token_data["preferred_username"]
        self._config.config["username"] = username
        if self._keyring_disabled:
            logging.warning("Not saving password as Keyring was disabled")
            return
        try:
            keyring.set_password(self._config.app_name, username, refresh_token)
        except KeyringError:
            # If the system keyring is broken, do not restrict remaining functionality
            logging.warn("Failed to store refresh token in system keyring")
        except DBusErrorResponse:
            logging.exception(SNAP_PASSWORD_MANAGER_SERVICE_ERROR)
            self._keyring_disabled = True

    def _clear_credentials(self) -> None:
        """Clear the username and auth token"""
        self._oauth_access_token_cache = ""
        self._oauth_access_token_data_cache = {}
        self._oauth_refresh_token_cache = ""
        self._oauth_refresh_token_data_cache = {}
        self.__dict__.pop("_jwks_client", None)
        self.__dict__.pop("_openid_config", None)
        if username := self._config.config.get("username"):
            if self._keyring_disabled:
                logging.warning("Not deleting password as Keyring was disabled")
                return
            try:
                keyring.delete_password(self._config.app_name, username)
            except PasswordDeleteError:
                pass
            except DBusErrorResponse:
                logging.exception(SNAP_PASSWORD_MANAGER_SERVICE_ERROR)
                self._keyring_disabled = True

    def _auth_server_request(self, url, data, headers=None):
        """Make a GraphQL server request with the cached auth token."""
        if not headers:
            headers = {**self._default_headers}
        if self._is_token_expired(self._oauth_access_token_data):
            updated = self._refresh_access_token()
            if not updated:
                raise WorkerWarning(self.access_expired_error)
        headers = {**headers, "Authorization": f"Bearer {self._oauth_access_token}"}
        return self._server_request(url, json=data, headers=headers)

    def _server_request(
        self,
        url: str,
        data: Dict[str, str] | None = None,
        json: Dict[str, str] | None = None,
        headers: Optional[Dict[str, str]] = None,
        raise_for_status: Optional[bool] = True,
    ) -> requests.Response:
        """Make a GraphQL server request that handles HTTP errors."""
        if not headers:
            headers = self._default_headers
        try:
            response = requests.post(
                url, data=data, json=json, headers=headers, timeout=10
            )
            if raise_for_status:
                response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            if err.response.status_code == 400 and err.request.url == self._graphql_url:
                logging.warning(f"GraphQL error: {err.response.content}")
                raise WorkerWarning(self.server_request_error) from err
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
            data = jwt.decode(token, options={"verify_signature": False}, leeway=60)
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
                leeway=60,
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
        if not self._oauth_refresh_token:
            return False
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
            logging.warn(f"Failed refreshing access token: {response.content}")
            return False
        tokens = response.json()
        if error := tokens.get("error"):
            logging.warning(
                f"Failed refreshing access token: {error} {tokens.get('error_description')}"
            )
            return False
        self._save_credentials(tokens["access_token"], tokens["refresh_token"])
        self._store_token_profile(self._oauth_access_token_data)
        logging.info("Successfully refreshed the access token")
        return True

    def _load_stored_refresh_token(self) -> bool:
        if self._keyring_disabled:
            return False
        username = self._config.config.get("username")
        if not username:
            return False
        credential = None
        try:
            credential = keyring.get_credential(self._config.app_name, username)
        except KeyringError:
            pass
        except DBusErrorResponse:
            logging.exception(SNAP_PASSWORD_MANAGER_SERVICE_ERROR)
            self._keyring_disabled = True
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
        return f"{self.server_urls.oauth_base_url}{self._oauth_device_path}"

    @property
    def _oauth_token_url(self) -> str:
        return f"{self.server_urls.oauth_base_url}{self._oauth_token_path}"

    @cached_property
    def _openid_config(self) -> Dict[str, str]:
        url = f"{self.server_urls.oauth_base_url}{self._openid_config_path}"
        return requests.get(url, self._default_headers).json()

    @cached_property
    def _jwks_client(self):
        """Collects the identity provider's public keys"""
        return jwt.PyJWKClient(self._openid_config["jwks_uri"])

    @property
    def _graphql_url(self) -> str:
        return f"{self.server_urls.core_base_url}{self._core_graphql_path}"

    @property
    def _default_headers(self) -> Dict[str, str]:
        parsed_core_url = urlparse(self.server_urls.core_base_url)
        return {"Host": parsed_core_url.netloc}

    @staticmethod
    def parse_sites(data: dict) -> List[SiteModel]:
        """Extracts sites from full GQL query."""
        return [
            SiteModel(id=i["node"]["id"], name=i["node"]["name"])
            for i in data["data"]["allSites"]["edges"]
        ]

    @classmethod
    def parse_controller_type_data(
        cls, data: dict
    ) -> tuple[dict[str, ControllerTypeModel], dict[str, FirmwareVariantModel]]:
        """Extracts controller type and firmware variants from GQL data."""
        ct_list = data["data"]["allControllerTypes"]["edges"]
        controller_types = {
            i["node"]["id"]: ControllerTypeModel(
                id=i["node"]["id"],
                name=i["node"]["name"],
                firmware_variants=cls.parse_firmware_variant_edges(
                    i["node"]["firmwareVariantEdges"]["edges"]
                ),
            )
            for i in ct_list
        }
        firmware_variants = {}
        for ct_data in ct_list:
            for fv_data in ct_data["node"]["firmwareVariantEdges"]["edges"]:
                fv_id: str = fv_data["node"]["firmwareVariant"]["id"]
                if fv_id in firmware_variants:
                    continue
                firmware_variant = FirmwareVariantModel(
                    id=fv_id, name=fv_data["node"]["firmwareVariant"]["name"]
                )
                firmware_variants[fv_id] = firmware_variant
        return (controller_types, firmware_variants)

    @staticmethod
    def parse_firmware_variant_edges(data: list) -> list[FirmwareVariantEdge]:
        """Expects data as [{"node: {...}, ...]"""
        return [
            FirmwareVariantEdge(
                firmware_variant_id=i["node"]["firmwareVariant"]["id"],
                priority=i["node"]["priority"],
            )
            for i in data
        ]

    @staticmethod
    def parse_bootloader_images(data: dict) -> dict[str, BootloaderImageModel]:
        """Extract bootloader images from GQL data."""
        return {
            i["node"]["id"]: BootloaderImageModel(
                id=i["node"]["id"],
                name=i["node"]["name"],
                version=Version(i["node"]["version"]),
                hash_sha3_512=i["node"]["hashSha3_512"],
                file="",
            )
            for i in data["data"]["allBootloaderImages"]["edges"]
        }

    @staticmethod
    def parse_firmware_images(
        data: dict, firmware_variant_id: str
    ) -> dict[str, FirmwareImageModel]:
        """Extract firmware images from GQL data."""
        return {
            i["node"]["id"]: FirmwareImageModel(
                id=i["node"]["id"],
                name=i["node"]["name"],
                version=Version(i["node"]["version"]),
                firmware_variant_id=firmware_variant_id,
                bootloader_image_id=i["node"]["bootloaderId"],
                hash_sha3_512=i["node"]["hashSha3_512"],
                file="",
            )
            for i in data["data"]["allFirmwareImages"]["edges"]
        }

    @classmethod
    def parse_controllers(cls, data: list) -> dict[str, ControllerModel]:
        """Expects data as [{"node": {...}}, ...]}"""
        return {i["node"]["id"]: cls.parse_controller(i["node"]) for i in data}

    @staticmethod
    def parse_controller(data: dict) -> ControllerModel:
        """Expects data as {"id: ..., "name": ...}"""
        if "firmwareImageId" in data:
            firmware_image_id = data["firmwareImageId"]
        else:
            if firmware_image := data.get("firmwareImage"):
                firmware_image_id = firmware_image["id"]
            else:
                firmware_image_id = None
        return ControllerModel(
            id=data["id"],
            name=data["name"],
            site_id=data["siteId"],
            controller_type_id=data["controllerTypeId"],
            firmware_image_id=firmware_image_id,
            partition_table_id=data["partitionTableId"],
            auth_token=data["authToken"]["key"] if data.get("authToken") else None,
        )

    @staticmethod
    def parse_controllers_firmware_image(data: list) -> dict[str, FirmwareImageModel]:
        """Expects data as [{"node": {...}}, ...]}"""
        firmware_images = {}
        for controller in data:
            firmware_image_data = controller["node"]["firmwareImage"]
            if not firmware_image_data:
                continue
            firmware_image_id = firmware_image_data["id"]
            if firmware_image_id in firmware_images:
                continue
            try:
                version = Version(firmware_image_data["version"])
            except ValueError:
                version = None
            firmware_image = FirmwareImageModel(
                id=firmware_image_id,
                name=firmware_image_data["name"],
                version=version,
                hash_sha3_512=firmware_image_data["hashSha3_512"],
                bootloader_image_id=firmware_image_data["bootloaderId"],
                firmware_variant_id=firmware_image_data["firmwareVariantId"],
                file="",
            )
            firmware_images.update({firmware_image_id: firmware_image})
        return firmware_images

    @property
    def getting_site_firmware_error(self):
        return QCoreApplication.translate(
            "server", "Error while getting site and firmware data."
        )

    @property
    def getting_controller_error(self):
        return QCoreApplication.translate(
            "server", "Error while getting controller data."
        )

    @property
    def too_many_controllers_error(self):
        return QCoreApplication.translate(
            "server",
            "Not all controllers for this site could be fetched. Please upgrade the Inamata Flasher.",
        )

    @property
    def getting_default_partition_table_error(self):
        return QCoreApplication.translate(
            "server", "Error while getting default partition table data."
        )

    @property
    def default_partition_table_not_found_error(self):
        return QCoreApplication.translate(
            "server", "Could not find default partition table"
        )

    @property
    def getting_partition_table_error(self):
        return QCoreApplication.translate(
            "server", "Error while getting partition table data."
        )

    @property
    def partition_table_not_found_error(self):
        return QCoreApplication.translate(
            "server", "Could not find partition table on server."
        )

    @property
    def controller_not_found_error(self):
        return QCoreApplication.translate(
            "server",
            "Could not find the controller. Please reload the controller data.",
        )

    @property
    def deleting_controller_error(self):
        return QCoreApplication.translate(
            "server",
            "Failed deleting controller. Check your permissions or contact your administrator.",
        )

    @property
    def auth_server_error(self):
        return QCoreApplication.translate(
            "server",
            "Failed connecting to the authentication server. Check your internet connection or contact Inamata.",
        )

    @property
    def downloading_firmware_error(self):
        return QCoreApplication.translate(
            "server",
            "Error downloading firmware. Not all required metadata found:",
        )

    @property
    def downloading_bootloader_error(self):
        return QCoreApplication.translate(
            "server",
            "Error downloading bootloader. Not all required metadata found:",
        )

    @property
    def download_failed_error(self):
        return QCoreApplication.translate(
            "server",
            "Failed downloading the file. Try refreshing, check your internet connection or contact support.",
        )

    @property
    def checksum_failed_error(self):
        return QCoreApplication.translate(
            "server",
            "Checksum of downloaded file did not match. Please try another version or contact support.",
        )

    @property
    def refreshing_firmware_url_failed_error(self):
        return QCoreApplication.translate(
            "server", "Error while refreshing the firmware URL. Please reload data."
        )

    @property
    def refreshing_bootloader_url_failed_error(self):
        return QCoreApplication.translate(
            "server", "Error while refreshing the bootloader URL. Please reload data."
        )

    @property
    def access_expired_error(self):
        return QCoreApplication.translate(
            "server", "Access has expired. Please log in again."
        )

    @property
    def server_request_error(self):
        return QCoreApplication.translate(
            "server",
            "An error occurred while requesting data from the server API."
            " Check that you're using an up-to-date version of the Inamata Flasher.",
        )
