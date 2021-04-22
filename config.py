import json
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
        self.config = self.load_config()

    def load_config(self) -> None:
        """Gets the stored config."""
        config = {}
        try:
            file = open(self._config_path, "r")
            config = json.load(file)
        except (JSONDecodeError, FileNotFoundError):
            pass
        finally:
            file.close()
        return config

    def save_config(self) -> None:
        """Overwrites the config file."""
        print("Saving config")
        with open(self._config_path, "w") as file:
            json.dump(self.config, file)
