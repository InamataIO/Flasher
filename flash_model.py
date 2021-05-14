import csv
import json
import logging
import os
import subprocess
from typing import List
from distutils.dir_util import copy_tree

from config import Config
from server_model import ServerModel
from wifi_model import WiFiModel
from worker import WorkerError, WorkerWarning, WorkerSignals


class FlashModel:
    """Used to flash the ESP32 controller."""

    # The path to the tool to generate the SPIFFS image
    _spiffs_tool_path = os.path.join(os.getcwd(), "esp-idf", "spiffsgen.py")
    # The subtype of the partition in the partition table to be used for the SPIFFS image
    _spiffs_partition_subtype_ = "spiffs"
    # The directory from which the files are copied to create the SPIFFS image
    _spiffs_source_dir_ = os.path.join(os.getcwd(), "spiffs")

    # The path to the tool to generate the partitions image
    _partitions_tool_path = os.path.join(os.getcwd(), "esp-idf", "gen_esp32part.py")
    # The offset in bytes where the partition image should be flashed to
    _partition_image_offset = 32768  # 0x8000

    # The subtype of the partition in the partition table to be used for the firmware image
    _firmware_partition_subtype_ = "ota_0"

    def __init__(self, server_model: ServerModel, config: Config):
        self._server_model = server_model
        self._config = config

        cache_dir = config.dirs.user_cache_dir

        # All files / dirs to create the SPIFFS image
        self._spiffs_dir = os.path.join(cache_dir, "spiffs_dir")
        self._spiffs_secret_path = os.path.join(self._spiffs_dir, "secrets.json")
        self._spiffs_image_path = os.path.join(cache_dir, "spiffs.bin")

        # All files / dirs to create the partition image
        self._partitions_csv_path = os.path.join(cache_dir, "partitions.csv")
        self._partitions_image_path = os.path.join(cache_dir, "partitions.bin")

    def flash_controller(
        self, controller: dict, wifi_aps: List[WiFiModel.AP], **kwargs
    ):
        """Flash a controller."""
        # Check if the controller has a partition table
        progress_callback = kwargs["progress_callback"]
        try:
            partition_table_id = controller["partitionTable"]["id"]
            if not partition_table_id:
                raise KeyError
        except KeyError:
            raise WorkerWarning("The controller does not have a partition table")
        partition_table = self._server_model.get_partition_table(partition_table_id)
        partitions = json.loads(partition_table["table"])
        spiffs_partition = next(i for i in partitions if i["name"] == "spiffs")
        spiffs_size = spiffs_partition["size"]
        self._create_partition_image(partitions)
        self._create_spiffs_image(spiffs_size, wifi_aps, controller)

        firmware_image = self._server_model.get_firmware_image(
            controller["firmwareImage"]["id"]
        )
        self._flash_controller(partitions, firmware_image, progress_callback)

    def _create_partition_image(self, partition_table: dict):
        """Generate a partition table image."""

        # Create the CSV which is used by the partition tool
        with open(self._partitions_csv_path, "w+") as csv_file:
            csv_writer = csv.writer(csv_file)
            for partition in partition_table:
                values = [
                    partition["name"],
                    partition["type"],
                    partition["subtype"],
                    partition["offset"],
                    partition["size"],
                    partition["flags"],
                ]
                csv_writer.writerow(values)

        # Create the binary partition table file
        process = subprocess.run(
            [
                "python",
                self._partitions_tool_path,
                self._partitions_csv_path,
                self._partitions_image_path,
            ],
            capture_output=True,
        )
        if process.returncode:
            logging.error(process.stderr)
            raise WorkerWarning("Error while generating the partitions image.")

    def _create_spiffs_image(
        self, image_size: int, wifi_aps: List[WiFiModel.AP], controller: dict
    ):
        """Generate a SPIFFS image."""

        try:
            secrets = {
                "wifi_aps": [
                    {"ssid": i.ssid, "password": i.password} for i in wifi_aps
                ],
                "ws_token": controller["authToken"]["key"],
                "core_domain": "core.openfarming.ai",
                "force_insecure": False,
            }
            os.makedirs(self._spiffs_dir, exist_ok=True)
            with open(self._spiffs_secret_path, "w+") as secret_file:
                json.dump(secrets, secret_file)
            copy_tree(self._spiffs_source_dir_, self._spiffs_dir)

            process = subprocess.run(
                [
                    "python",
                    self._spiffs_tool_path,
                    str(image_size),
                    self._spiffs_dir,
                    self._spiffs_image_path,
                ],
                capture_output=True,
            )
            if process.stderr:
                logging.error(process.stderr)
                raise WorkerWarning("Error while generating the SPIFFS image.")
        finally:
            try:
                os.remove(self._spiffs_secret_path)
            except FileNotFoundError:
                pass

    def _flash_controller(
        self, partitions: dict, firmware: dict, progress: WorkerSignals
    ):
        """Flash the controller with the generate images."""
        firmware_image_path = self._server_model.get_firmware_image_path(firmware)
        if not os.path.isfile(firmware_image_path):
            logging.error(f"Could not find firmware image at: {firmware_image_path}")
            raise WorkerError(
                "Firmware image could not be found. Please refresh the cached files."
            )
        firmware_partition = next(
            i for i in partitions if i["subtype"] == self._firmware_partition_subtype_
        )
        spiffs_partition = next(
            i for i in partitions if i["subtype"] == self._spiffs_partition_subtype_
        )
        # Flash the partition table, firmware and SPIFFS image
        process = subprocess.Popen(
            [
                "esptool.py",
                "--baud",
                str(921600),
                "write_flash",
                str(self._partition_image_offset),
                self._partitions_image_path,
                str(spiffs_partition["offset"]),
                self._spiffs_image_path,
                str(firmware_partition["offset"]),
                firmware_image_path,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
        while True:
            output = process.stdout.readline()
            if output == "" and process.poll() is not None:
                break
            if output and output.startswith("Writing at "):
                offset = int(output.split("Writing at ")[1][0:10], 16)
                if offset >= firmware_partition["offset"]:
                    percent = int(output.split("(")[1].split("%")[0])
                    progress.emit(percent)
        if process.poll():
            logging.error(process.stderr)
            raise WorkerError("Failed to flash the controller. Please try again.")            
