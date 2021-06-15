import json
import logging
import os
import pathlib
from json import JSONDecodeError
import shutil
from typing import List, Optional

from appdirs import AppDirs


class Config:
    """Used to store and load configurations."""

    app_name = "ofai-flasher"
    app_author = "protohaus"
    dirs = AppDirs(app_name, app_author)

    def __init__(self):
        """Load the config from file in the platform-specific config folder."""
        pathlib.Path(self.dirs.user_config_dir).mkdir(parents=True, exist_ok=True)
        self._config_path = os.path.join(self.dirs.user_config_dir, "config.json")
        logging.info("Config path: %s", self._config_path)
        logging.info("Cache dir: %s", self.dirs.user_cache_dir)
        self.config = self.load_config()

    def save_controllers(self, controllers: List[dict], site_id: str) -> None:
        """Save controllers to cache. Clears existing controllers for a site."""
        if "controllers" not in self.config:
            self.config["controllers"] = {}
        controllers.sort(key=self.controller_key)
        self.config["controllers"].update({site_id: controllers})

    def save_controller(self, controller: dict, site_id: str) -> None:
        """Save a controller to cache."""
        sites = self.config.get("controllers", {})
        controllers = sites.get(site_id, [])
        # Remove duplicates of the new controller, if present
        controllers = [i for i in controllers if i["id"] != controller["id"]]
        # Add to and sort the list of controllers
        controllers.append(controller)
        controllers.sort(key=self.controller_key)
        # Save the site-partitioned controller list
        sites.update({site_id: controllers})
        self.config["controllers"] = sites

    def get_controller(self, controller_id: str, site_id: str) -> Optional[dict]:
        """Get a controller."""
        if sites := self.config.get("controllers"):
            controllers = sites.get(site_id, [])
            return next(i for i in controllers if i["id"] == controller_id)
        return None

    def get_controllers(self, site_id: str) -> Optional[List[dict]]:
        """Get all controllers for a site."""
        if sites := self.config.get("controllers"):
            return sites.get(site_id)
        return None

    def load_config(self) -> None:
        """Gets the stored config."""
        try:
            with open(self._config_path, "r") as file:
                config = json.load(file)
        except (JSONDecodeError, FileNotFoundError):
            config = {}
        return config

    def save_config(self) -> None:
        """Overwrites the config file."""
        print("Saving config")
        with open(self._config_path, "w") as file:
            json.dump(self.config, file)

    def clear_cached_data(self) -> None:
        """Clears cache incl. sites, firmware images and controller data."""
        self.config.pop("sites", None)
        self.config.pop("controllers", None)
        self.config.pop("controller", None)
        self.config.pop("firmwareImages", None)
        self.config.pop("bootloaderImages", None)
        self.config.pop("partitionTables", None)
        shutil.rmtree(self.dirs.user_cache_dir, ignore_errors=True)

    @staticmethod
    def controller_key(controller):
        """Used to sort controller lists."""
        return controller["siteEntity"]["name"]
