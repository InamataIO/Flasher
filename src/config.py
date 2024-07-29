import json
import logging
import os
import shutil
from collections import defaultdict
from dataclasses import dataclass, field
from functools import cached_property, lru_cache
from json import JSONDecodeError
from pathlib import Path

from platformdirs import PlatformDirs
from semantic_version import Version


@dataclass
class FirmwareVariantEdge:
    firmware_variant_id: str
    priority: int


@dataclass
class ControllerTypeModel:
    id: str
    name: str
    firmware_variants: list[FirmwareVariantEdge] = field(default_factory=list)


@dataclass
class ControllerModel:
    id: str
    name: str
    site_id: str
    controller_type_id: str
    firmware_image_id: str
    partition_table_id: str
    auth_token: str | None = field(default=None)


@dataclass
class FirmwareVariantModel:
    id: str
    name: str
    firmware_image_ids: list[str] = field(default_factory=list)


@dataclass
class BaseImageModel:
    id: str
    name: str
    version: Version | None
    hash_sha3_512: str
    file: str


@dataclass
class BootloaderImageModel(BaseImageModel):
    pass


@dataclass
class FirmwareImageModel(BaseImageModel):
    bootloader_image_id: str
    firmware_variant_id: str


@dataclass
class SiteModel:
    id: str
    name: str


class Config:
    """Used to store and load configurations."""

    app_name = "inamata-flasher"
    app_author = "inamata"
    dirs = PlatformDirs(app_name, app_author)
    supported_controller_types = ["ESP32", "Norvi Agent 1"]

    def __init__(self, app_version):
        """Load the config from file in the platform-specific config folder."""
        Path(self.dirs.user_config_dir).mkdir(parents=True, exist_ok=True)
        self._config_path = os.path.join(self.dirs.user_config_dir, "config.json")
        logging.info("Config path: %s", self._config_path)
        logging.info("Cache dir: %s", self.dirs.user_cache_dir)
        self.config = self.load_config()
        self._init_cache()

        self.fonts_folder = self.root_folder / "fonts"
        self.images_folder = self.root_folder / "images"
        self.littlefs_folder = self.root_folder / "littlefs_partition"
        self.translations_folder = self.root_folder / "translations"
        self.uis_folder = self.root_folder / "uis"
        self.app_version = app_version

        self.is_snap = bool(os.getenv("SNAP"))

    @property
    def users_name(self) -> str:
        """Tries to return the user's name, else their username or a blank string."""
        if name := self.config.get("name"):
            return name
        elif username := self.config.get("username"):
            return username
        return ""

    @cached_property
    def root_folder(self):
        if (Path(__file__).parent / "uis").exists():
            root_folder = Path(__file__).parent
        else:
            root_folder = Path(__file__).parent.parent
        return root_folder

    def cache_controllers(self, controllers: dict[str, ControllerModel]) -> None:
        """Save controllers to cache."""
        self._cache["controllers"].update(controllers)

    def get_controller(self, controller_id: str) -> ControllerModel | None:
        """Get a cached controller."""
        return self._cache["controllers"].get(controller_id)

    def get_controllers_by_site(self, site_id: str) -> list[ControllerModel]:
        """Get all cached controllers for a site."""
        return [c for c in self._cache["controllers"].values() if c.site_id == site_id]

    def cache_sites(self, sites: list[SiteModel]) -> None:
        """Cache sites."""
        self._cache["sites"].update({s.id: s for s in sites})

    def has_cached_sites(self) -> bool:
        """Checks if sites have been cached."""
        return bool(self._cache["sites"])

    def get_sites(self) -> list[SiteModel]:
        """Get all cached sites."""
        return [s for s in self._cache["sites"].values()]

    def cache_controller_types(
        self, controller_types: dict[str, ControllerTypeModel]
    ) -> None:
        """Cache controller types."""
        self._cache["controllerTypes"].update(controller_types)

    def has_cached_controller_types(self) -> bool:
        """Checks if controller types have been cached."""
        return bool(self._cache["controllerTypes"])

    def get_controller_types(self) -> list[ControllerTypeModel]:
        """Get all cached controller types."""
        return self._cache["controllerTypes"].values()

    def get_controller_type(
        self, controller_type_id: str
    ) -> ControllerTypeModel | None:
        return self._cache["controllerTypes"].get(controller_type_id)

    def cache_firmware_variants(
        self, firmware_variants: dict[str, FirmwareVariantModel]
    ) -> None:
        """Cache firmware variants."""
        self._cache["firmwareVariants"].update(firmware_variants)

    def cache_firmware_images_in_variant(
        self, firmware_variant_id: str, firmware_image_ids: list[str]
    ) -> None:
        firmware_variant = self._cache["firmwareVariants"].get(firmware_variant_id)
        if not firmware_variant:
            return
        firmware_variant.firmware_image_ids = firmware_image_ids

    def get_firmware_variants(self) -> list[FirmwareVariantModel]:
        """Get all cached firmware variants."""
        return self._cache["firmwareVariants"].values()

    @lru_cache(maxsize=10)
    def get_firmware_variants_for_controller_type(
        self, controller_type_id: str
    ) -> list[FirmwareVariantModel]:
        """Get firmware variants for a controller type, sorted by priority."""
        controller_type: ControllerTypeModel = self._cache["controllerTypes"].get(
            controller_type_id, ControllerTypeModel(id="", name="")
        )
        firmware_variant_edges = {
            fw_variant_edge.firmware_variant_id: fw_variant_edge.priority
            for fw_variant_edge in controller_type.firmware_variants
        }
        firmware_variants = [
            v
            for k, v in self._cache["firmwareVariants"].items()
            if k in firmware_variant_edges.keys()
        ]
        firmware_variants.sort(key=lambda i: firmware_variant_edges[i.id], reverse=True)
        return firmware_variants

    def get_firmware_variant(
        self, firmware_variant_id: str
    ) -> FirmwareVariantModel | None:
        return self._cache["firmwareVariants"].get(firmware_variant_id)

    def cache_bootloader_images(
        self, bootloader_images: dict[str, BootloaderImageModel]
    ) -> None:
        """Cache firmware images."""
        self._cache["bootloaderImages"].update(bootloader_images)

    def get_bootloader_image(
        self, bootloader_image_id: str
    ) -> BootloaderImageModel | None:
        return self._cache["bootloaderImages"].get(bootloader_image_id)

    def cache_firmware_images(
        self, firmware_images: dict[str, FirmwareImageModel]
    ) -> None:
        """Cache firmware images."""
        self._cache["firmwareImages"].update(firmware_images)

    @lru_cache(maxsize=10)
    def get_firmware_images_for_variant(
        self, firmware_variant_id: str
    ) -> list[FirmwareImageModel]:
        firmware_variant = self._cache["firmwareVariants"].get(firmware_variant_id)
        if not firmware_variant:
            return
        firmware_images = [
            v
            for k, v in self._cache["firmwareImages"].items()
            if k in firmware_variant.firmware_image_ids
        ]
        firmware_images.sort(key=lambda i: i.version, reverse=True)
        return firmware_images

    def get_firmware_image(self, firmware_image_id: str) -> FirmwareImageModel | None:
        return self._cache["firmwareImages"].get(firmware_image_id)

    def load_config(self) -> dict:
        """Gets the stored config."""
        try:
            with open(self._config_path, "r") as file:
                config = json.load(file)
        except (JSONDecodeError, FileNotFoundError):
            config = {}
        return config

    def save_config(self) -> None:
        """Overwrites the config file."""
        Path(self.dirs.user_config_dir).mkdir(parents=True, exist_ok=True)
        with open(self._config_path, "w") as file:
            self.config["versions"] = {"app": self.app_version, "syntax": 1}
            json.dump(self.config, file)

    def clear_stored_data(self) -> None:
        """Clears all local data."""
        self.config = {}
        shutil.rmtree(self.dirs.user_data_dir, ignore_errors=True)
        shutil.rmtree(self.dirs.site_data_dir, ignore_errors=True)
        shutil.rmtree(self.dirs.user_config_dir, ignore_errors=True)
        shutil.rmtree(self.dirs.site_config_dir, ignore_errors=True)
        shutil.rmtree(self.dirs.user_cache_dir, ignore_errors=True)
        shutil.rmtree(self.dirs.user_state_dir, ignore_errors=True)
        shutil.rmtree(self.dirs.user_log_dir, ignore_errors=True)

    def clear_cached_data(self) -> None:
        """Clears cache incl. firmware images and controller data."""
        self.get_firmware_variants_for_controller_type.cache_clear()
        self.get_firmware_images_for_variant.cache_clear()
        self._init_cache()
        shutil.rmtree(self.dirs.user_cache_dir, ignore_errors=True)

    def _init_cache(self) -> None:
        self._cache = defaultdict(dict)
