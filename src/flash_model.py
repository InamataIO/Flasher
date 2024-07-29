import csv
import json
import logging
import os
import platform
import subprocess
import sys
from contextlib import redirect_stderr
from distutils.dir_util import copy_tree
from io import StringIO
from pathlib import Path
from typing import List

import esptool
import serial.tools.list_ports as list_ports
from littlefs import LittleFS, LittleFSError
from PySide6.QtCore import QCoreApplication
from serial.tools.list_ports_common import ListPortInfo

from config import Config, ControllerModel
from esp_idf import gen_esp32part
from server_model import ServerModel
from wifi_model import WiFiModel
from worker import WorkerError, WorkerSignals, WorkerWarning

if platform.system() == "Linux":
    import grp


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

    # The subtype of the partition in the partition table to be used for the LittleFS image
    _littlefs_partition_subtype = "spiffs"
    # The block size in bytes for the LittleFS image
    _littlefs_block_size = 4096

    # The offset in bytes where the bootloader image should be flashed to
    _bootloader_image_offset = 4096  # 0x1000

    # The offset in bytes of the partition image (valid for ESP32)
    # https://docs.espressif.com/projects/esp8266-rtos-sdk/en/latest/api-guides/partition-tables.html
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

        # The directory from which the files are copied to create the LittleFS image
        self._littlefs_source_dir = self._config.littlefs_folder

        # All files / dirs to create the LittleFS image
        self._littlefs_dir = os.path.join(cache_dir, "littlefs")
        self._littlefs_secret_path = os.path.join(self._littlefs_dir, "secrets.json")
        self._littlefs_image_path = os.path.join(cache_dir, "littlefs.bin")

        # All files / dirs to create the partition image
        self._partitions_csv_path = os.path.join(cache_dir, "partitions.csv")
        self._partitions_image_path = os.path.join(cache_dir, "partitions.bin")

    def get_serial_ports(self) -> list[ListPortInfo]:
        try:
            return list_ports.comports()
        except TypeError as err:
            if self._config.is_snap:
                logging.warning(f"{self.snap_listing_com_port_failed_error}\n\n{err}")
            else:
                logging.warning(f"{self.listing_com_port_failed_error}\n\n{err}")
        except Exception as err:
            logging.warning(f"{self.listing_com_port_failed_error}\n\n{err}")
        return []

    def check_permissions(self, **kwargs) -> str:
        """Returns an error string if permissions are missing."""
        if platform.system() == "Linux":
            groups = [grp.getgrgid(g).gr_name for g in os.getgroups()]
            if "dialout" not in groups:
                return self.linux_dialout_group_error
        if self._config.is_snap:
            result = subprocess.run(["snapctl", "is-connected", "raw-usb"])
            if result.returncode == 1:
                return self.snap_listing_com_port_failed_error
        return ""

    def flash_controller(
        self, controller: ControllerModel, wifi_aps: List[WiFiModel.AP], **kwargs
    ):
        """Flash a controller."""
        # Check if the controller has a partition table
        progress_callback = kwargs["progress_callback"]
        partition_table = self._server_model.get_partition_table(
            controller.partition_table_id
        )
        partitions = partition_table["table"]
        # Partition type is "spiffs"
        # https://docs.platformio.org/en/latest/platforms/espressif32.html#uploading-files-to-file-system
        littlefs_partition = next(
            i for i in partitions if i["name"] == "spiffs" or i["name"] == "littlefs"
        )
        # The size of the LittleFS partition in bytes
        littlefs_size = littlefs_partition["size"]
        self._create_partition_image(partitions)
        self._create_littlefs_image(littlefs_size, wifi_aps, controller)

        firmware_image = self._config.get_firmware_image(controller.firmware_image_id)
        bootloader_image: dict | None = None
        if bootloader_id := firmware_image.bootloader_image_id:
            bootloader_image = self._config.get_bootloader_image(bootloader_id)
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
        except SystemExit:
            logging.error(stderr)
            raise WorkerWarning(self.partition_gen_error)
        finally:
            # Restore the original cmdline arguments
            sys.argv = original_argv

    def _create_littlefs_image(
        self, image_size: int, wifi_aps: List[WiFiModel.AP], controller: ControllerModel
    ) -> None:
        """Generate a LittleFS image."""

        try:
            # Create the dict with the secrets to be flashed
            secrets = {
                "wifi_aps": [
                    {"ssid": i.ssid, "password": i.password} for i in wifi_aps
                ],
                "ws_token": controller.auth_token,
                "core_domain": self._server_model.core_domain,
                "secure_url": self._server_model.is_core_url_secure,
                "name": controller.name,
            }
            # Make a directory to place all files in for the LittleFS image
            os.makedirs(self._littlefs_dir, exist_ok=True)
            # Store the secret dict as a json file. Overwrite file if one exists
            with open(self._littlefs_secret_path, "w+") as secret_file:
                json.dump(secrets, secret_file)
            # Copy over other files to be added to the SPIFFS image
            copy_tree(self._littlefs_source_dir, self._littlefs_dir)

            # ESP32's have a separate partition table, ESP8266's is integrated in the firmware
            if controller.partition_table_id:
                # Ensure that the image size is a multiple of the block size
                if image_size % self._littlefs_block_size:
                    raise WorkerError(
                        self.image_size_error(image_size, self._littlefs_block_size)
                    )
                block_count = int(image_size / self._littlefs_block_size)
                fs = LittleFS(
                    block_size=self._littlefs_block_size, block_count=block_count
                )
            else:
                # Create the file system for the ESP8266
                fs = LittleFS(block_size=8192, block_count=125, name_max=32)

            # Copy all files from the littlefs folder to the LittleFS image
            pathlist = Path(self._littlefs_dir).glob("**/*")
            for path in pathlist:
                # Workaround as lfs.cpython-310-x86_64-linux-gnu.so is copied into the
                # littlefs folder by pyinstaller
                if str(path).endswith(".so"):
                    continue
                relative_path = path.relative_to(self._littlefs_dir)
                if path.is_dir():
                    fs.mkdir(str(relative_path))
                    continue
                with path.open("rb") as source, fs.open(
                    str(relative_path), "wb"
                ) as target:
                    target.write(source.read())
            for root, dirs, files in fs.walk("."):
                logging.info(f"LittleFS: root {root} dirs {dirs} files {files}")
            # Clear if it exists and then save the LittleFS image to the file
            Path(self._littlefs_image_path).unlink(missing_ok=True)
            with open(self._littlefs_image_path, "wb") as f:
                f.write(fs.context.buffer)
        except (LittleFSError, OSError, ValueError) as err:
            raise WorkerError(f"{self.littlefs_gen_error} {type(err)}: {err}") from err
        finally:
            # Try to delete the created secret file
            try:
                os.remove(self._littlefs_secret_path)
            except FileNotFoundError:
                pass

    def _flash_controller(
        self,
        partitions: dict,
        firmware: dict,
        bootloader: dict | None,
        progress: WorkerSignals,
    ):
        """Flash the controller with the generate images."""
        firmware_image_path = self._server_model.get_image_path(firmware)
        if not os.path.isfile(firmware_image_path):
            logging.error(f"Could not find firmware image at: {firmware_image_path}")
            raise WorkerError(self.firmware_not_found_error)
        if bootloader:
            bootloader_image_path = self._server_model.get_image_path(bootloader)
            if not os.path.isfile(bootloader_image_path):
                logging.error(
                    f"Could not find bootloader image at: {bootloader_image_path}"
                )
                raise WorkerError(self.bootloader_not_found_error)
            firmware_partition = next(
                i
                for i in partitions
                if i["subtype"] == self._firmware_partition_subtype
            )
            littlefs_partition = next(
                i
                for i in partitions
                if i["subtype"] == self._littlefs_partition_subtype
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
        # Flash the partition table, firmware and LittleFS image
        # WORKAROUND: Place the LittleFS flash command before the image flash command
        esptool_flash_args = ["--baud", str(self._esptool_baud_rate), "write_flash"]
        if bootloader:
            esptool_flash_args.extend(
                [
                    str(self._partition_image_offset),
                    self._partitions_image_path,
                    str(self._bootloader_image_offset),
                    bootloader_image_path,
                    str(firmware_partition["offset"]),
                    firmware_image_path,
                    str(littlefs_partition["offset"]),
                    self._littlefs_image_path,
                ]
            )
        else:
            esptool_flash_args.extend(
                [
                    "0x0",
                    firmware_image_path,
                ]
            )

        # Capture stdout to track progress. stderr to get error messages
        sys.stdout = EsptoolOutputHandler(progress)
        stderr = StringIO()
        try:
            with redirect_stderr(stderr):
                if bootloader:
                    esptool.main(esptool_erase_otadata_args)
                esptool.main(esptool_flash_args)
        except Exception as err:
            logging.error(stderr)
            raise WorkerError(self._get_flash_error_msg(err)) from err
        finally:
            # Restore the stdout after flashing
            sys.stdout = sys.__stdout__

    def _get_flash_error_msg(self, err: Exception) -> str:
        if self._config.is_snap:
            return f"{self.snap_flashing_failed_error}\n\n{err}"
        return f"{self.flashing_failed_error}\n\n{err}"

    @property
    def partition_gen_error(self):
        return QCoreApplication.translate(
            "flash", "Error while generating the partitions image."
        )

    def image_size_error(self, image_size, block_size):
        return QCoreApplication.translate(
            "flash",
            "Image size (%n bytes) is not a multiple of the block size (%n bytes)",
            "",
            image_size,
            block_size,
        )

    @property
    def littlefs_gen_error(self):
        return QCoreApplication.translate(
            "flash", "Error while generating LittleFS image:"
        )

    @property
    def firmware_not_found_error(self):
        return QCoreApplication.translate(
            "flash",
            "Firmware image could not be found. Please refresh the cached files.",
        )

    @property
    def bootloader_not_found_error(self):
        return QCoreApplication.translate(
            "flash",
            "Bootloader image could not be found. Please refresh the cached files.",
        )

    @property
    def snap_flashing_failed_error(self):
        return QCoreApplication.translate(
            "flash",
            """Flashing failed
1. Check that the microcontroller is plugged in
2. For Snaps (Ubuntu Store) enable serial port access
 - Run in a terminal: snap connect inamata-flasher:raw-usb
 - Restart the app
3. Open a bug report or ask for support in the forum.

https://github.com/InamataIO/Flasher
https://www.inamata.io/forum/""",
        )

    @property
    def flashing_failed_error(self):
        return QCoreApplication.translate(
            "flash",
            """Flashing failed
1. Check that the microcontroller is plugged in
2. Open a bug report or ask for support in the forum.

https://github.com/InamataIO/Flasher
https://www.inamata.io/forum/""",
        )

    @property
    def linux_dialout_group_error(self):
        return QCoreApplication.translate(
            "flash",
            """User is missing permissions
1. Add the user to the dialout group (access serial ports)
  - Run in a terminal: sudo usermod -a -G dialout $USER
2. Log out and back in again""",
        )

    @property
    def snap_listing_com_port_failed_error(self):
        return QCoreApplication.translate(
            "flash",
            """Listing COM / serial ports failed
For Snap installations:
 - Run in a terminal: snap connect inamata-flasher:raw-usb
 - Restart the app""",
        )

    @property
    def listing_com_port_failed_error(self):
        return QCoreApplication.translate("flash", "Error when listing COM ports:")
