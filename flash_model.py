import csv
import json
import logging
import os
import sys
from contextlib import redirect_stderr
from distutils.dir_util import copy_tree
from io import StringIO
from typing import List

import esptool

from config import Config, ControllerModel
from esp_idf import gen_esp32part, spiffsgen
from server_model import ServerModel
from wifi_model import WiFiModel
from worker import WorkerError, WorkerSignals, WorkerWarning


class EsptoolOutputHandler:
    """Handle the output of the esptool."""

    def __init__(self, progress):
        self.progress = progress

    def write(self, output: str):
        """Capture stdout to update flash progress."""
        if sys.__stdout__:
            sys.__stdout__.write(output)
        if output and output.startswith("Writing at "):
            if "0x00008000..." in output:
                self.progress.emit(5)
            elif "0x00001000..." in output:
                self.progress.emit(10)
            elif "0x003d0000..." in output:
                self.progress.emit(15)
            else:
                percent = int(output.split("(")[1].split("%")[0])
                mapped_percent = percent / 100 * 80 + 20
                self.progress.emit(mapped_percent)

    def flush(self):
        """Required by the interface."""
        if sys.__stdout__:
            sys.__stdout__.flush()

    def isatty(self):
        """Used by esptool."""
        return False


class FlashModel:
    """Used to flash the ESP32 controller.

    Standard partition table:
    - 0x1000 - **2nd stage bootloader
    - 0x8000 - partition table
    - 0xe000 - **otadata
    - 0x10000 - program
    - 0x3D0000 - SPIFFS
    """

    # The subtype of the partition in the partition table to be used for the SPIFFS image
    _spiffs_partition_subtype = "spiffs"
    # The directory from which the files are copied to create the SPIFFS image
    _spiffs_source_dir = os.path.join(os.getcwd(), "spiffs")

    # The offset in bytes where the bootloader image should be flashed to
    _bootloader_image_offset = 4096  # 0x1000

    # The offset in bytes where the partition image should be flashed to
    _partition_image_offset = 32768  # 0x8000

    # The subtype of the partition in the partition table to be used for the firmware image
    _firmware_partition_subtype = "ota_0"

    # The type and subtype of the otadata partition table (which OTA app slot to boot)
    _otadata_partition_type = "data"
    _otadata_partition_subtype = "ota"

    # ESP tool flash baud rate
    _esptool_baud_rate = 921600

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
        self, controller: ControllerModel, wifi_aps: List[WiFiModel.AP], **kwargs
    ):
        """Flash a controller."""
        # Check if the controller has a partition table
        progress_callback = kwargs["progress_callback"]
        partition_table = self._server_model.get_partition_table(
            controller.partition_table_id
        )
        partitions = json.loads(partition_table["table"])
        spiffs_partition = next(i for i in partitions if i["name"] == "spiffs")
        spiffs_size = spiffs_partition["size"]
        self._create_partition_image(partitions)
        self._create_spiffs_image(spiffs_size, wifi_aps, controller)

        firmware_image = self._server_model.get_firmware_image(
            controller.firmware_image_id
        )
        bootloader_image = self._server_model.get_bootloader_image(
            firmware_image["bootloader"]["id"]
        )
        self._flash_controller(
            partitions, firmware_image, bootloader_image, progress_callback
        )

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
        # Store the original cmdline arguments, to restore them
        original_argv = sys.argv
        sys.argv = ["", self._partitions_csv_path, self._partitions_image_path]
        stderr = StringIO()
        # Catch the exit exception if an error occurs
        try:
            # Catch the stderr to log errors
            with redirect_stderr(stderr):
                gen_esp32part.main()
        except SystemExit as err:
            logging.error(stderr)
            raise WorkerWarning("Error while generating the partitions image.")
        finally:
            # Restore the original cmdline arguments
            sys.argv = original_argv

    def _create_spiffs_image(
        self, image_size: int, wifi_aps: List[WiFiModel.AP], controller: ControllerModel
    ):
        """Generate a SPIFFS image."""

        try:
            # Create the dict with the secrets to be flashed
            secrets = {
                "wifi_aps": [
                    {"ssid": i.ssid, "password": i.password} for i in wifi_aps
                ],
                "ws_token": controller.auth_token,
                "core_domain": self._server_model.core_domain,
                "secure_url": self._server_model.is_core_url_secure,
            }
            # Make a directory to place all files in for the SPIFFS image
            os.makedirs(self._spiffs_dir, exist_ok=True)
            # Store the secret dict as a json file
            with open(self._spiffs_secret_path, "w+") as secret_file:
                json.dump(secrets, secret_file)
            # Copy over other files to be added to the SPIFFS image
            copy_tree(self._spiffs_source_dir, self._spiffs_dir)

            # Prepare to run the SPIFFS generator. Save the cmdline args to be restored
            original_argv = sys.argv
            sys.argv = ["", str(image_size), self._spiffs_dir, self._spiffs_image_path]
            stderr = StringIO()
            # Handle the exit exception, that is thrown on errors
            try:
                # Capture the stderr output to log errors
                with redirect_stderr(stderr):
                    spiffsgen.main()
            except SystemExit as err:
                # Abort the flash process if unable to create the SPIFFS image
                logging.error(stderr)
                raise WorkerWarning("Error while generating the SPIFFS image.")
            finally:
                # Restore the original cmdline args
                sys.argv = original_argv
        finally:
            # Try to delete the created secret file
            try:
                os.remove(self._spiffs_secret_path)
            except FileNotFoundError:
                pass

    def _flash_controller(
        self,
        partitions: dict,
        firmware: dict,
        bootloader: dict,
        progress: WorkerSignals,
    ):
        """Flash the controller with the generate images."""
        firmware_image_path = self._server_model.get_image_path(firmware)
        if not os.path.isfile(firmware_image_path):
            logging.error(f"Could not find firmware image at: {firmware_image_path}")
            raise WorkerError(
                "Firmware image could not be found. Please refresh the cached files."
            )
        bootloader_image_path = self._server_model.get_image_path(bootloader)
        if not os.path.isfile(bootloader_image_path):
            logging.error(
                f"Could not find bootloader image at: {bootloader_image_path}"
            )
            raise WorkerError(
                "Bootloader image could not be found. Please refresh the cached files."
            )
        firmware_partition = next(
            i for i in partitions if i["subtype"] == self._firmware_partition_subtype
        )
        spiffs_partition = next(
            i for i in partitions if i["subtype"] == self._spiffs_partition_subtype
        )
        otadata_partition = next(
            i
            for i in partitions
            if i["type"] == self._otadata_partition_type
            and i["subtype"] == self._otadata_partition_subtype
        )
        # Erase the OTA data partition
        esptool_erase_otadata_args = [
            "--baud",
            str(self._esptool_baud_rate),
            "erase_region",
            str(otadata_partition["offset"]),
            str(otadata_partition["size"]),
        ]
        # Flash the partition table, firmware and SPIFFS image
        # WORKAROUND: Place the SPIFFS flash command before the image flash command
        esptool_flash_args = [
            "--baud",
            str(self._esptool_baud_rate),
            "write_flash",
            str(self._partition_image_offset),
            self._partitions_image_path,
            str(self._bootloader_image_offset),
            bootloader_image_path,
            str(spiffs_partition["offset"]),
            self._spiffs_image_path,
            str(firmware_partition["offset"]),
            firmware_image_path,
        ]
        # Capture stdout to track progress. stderr to get error messages
        sys.stdout = EsptoolOutputHandler(progress)
        stderr = StringIO()
        try:
            with redirect_stderr(stderr):
                esptool.main(esptool_erase_otadata_args)
                esptool.main(esptool_flash_args)
        except SystemExit as err:
            logging.error(stderr)
            raise WorkerError("Failed to flash the controller. Please try again.")
        finally:
            # Restore the stdout after flashing
            sys.stdout = sys.__stdout__
