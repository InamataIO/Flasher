import json
import logging
import os
import shutil
from dataclasses import dataclass, field
from functools import cached_property
from json import JSONDecodeError
from pathlib import Path
from typing import Dict, List, Optional

from appdirs import AppDirs


@dataclass
class ControllerModel:
    id: str
    name: str
    site_id: str
    controller_type_id: str
    firmware_image_id: str
    partition_table_id: str
    auth_token: str = field(default=None)


@dataclass
class SiteModel:
    id: str
    name: str


class Config:
    """Used to store and load configurations."""

    app_name = "inamata-flasher"
    app_author = "inamata"
    dirs = AppDirs(app_name, app_author)

    def __init__(self, app_version):
        """Load the config from file in the platform-specific config folder."""
        Path(self.dirs.user_config_dir).mkdir(parents=True, exist_ok=True)
        self._config_path = os.path.join(self.dirs.user_config_dir, "config.json")
        logging.info("Config path: %s", self._config_path)
        logging.info("Cache dir: %s", self.dirs.user_cache_dir)
        self.config = self.load_config()
        self._init_cache()

        self.uis_folder = self.root_folder / "uis"
        self.fonts_folder = self.root_folder / "fonts"
        self.images_folder = self.root_folder / "images"
        self.littlefs_folder = self.root_folder / "littlefs_partition"
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

    def cache_controllers(self, controllers: List[ControllerModel]) -> None:
        """Save controllers to cache."""
        self._cache["controllers"].update({c.id: c for c in controllers})

    def get_controller(self, controller_id: str) -> Optional[ControllerModel]:
        """Get a cached controller."""
        return self._cache["controllers"].get(controller_id)

    def get_controllers_by_site(self, site_id: str) -> List[ControllerModel]:
        """Get all cached controllers for a site."""
        return [c for c in self._cache["controllers"].values() if c.site_id == site_id]

    def cache_sites(self, sites: List[SiteModel]) -> None:
        """Cache sites."""
        self._cache["sites"].update({s.id: s for s in sites})

    def has_cached_sites(self) -> bool:
        """Checks if sites have been cached."""
        return bool(self._cache["sites"])

    def get_sites(self) -> List[SiteModel]:
        """Get all cached sites."""
        return [s for s in self._cache["sites"].values()]

    def load_config(self) -> Dict:
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
        self._init_cache()
        self.config.pop("firmwareImages", None)
        self.config.pop("bootloaderImages", None)
        self.config.pop("partitionTables", None)
        shutil.rmtree(self.dirs.user_cache_dir, ignore_errors=True)

    def _init_cache(self) -> None:
        self._cache = {"controllers": {}, "sites": {}}
