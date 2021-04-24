import json
import logging
import os
import pathlib
from json import JSONDecodeError

from appdirs import AppDirs


class DSFlasherConfig:
    """Used to store and load configurations."""

    app_name = "ds-flasher"
    app_author = "device-stacc"
    dirs = AppDirs(app_name, app_author)

    def __init__(self):
        """Load the config from file in the platform-specific config folder."""
        pathlib.Path(self.dirs.user_config_dir).mkdir(parents=True, exist_ok=True)
        self._config_path = os.path.join(self.dirs.user_config_dir, "config.json")
        logging.info("Config path: %s", self._config_path)
        self.config = self.load_config()

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
        self.config.pop("firmware_images", None)