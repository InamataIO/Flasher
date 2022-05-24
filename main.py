#!/usr/bin/env python

"""Register ESP32's with the Inamata Server

Inamata Flasher is a tool for flashing the Inamata controller firmware on ESP32
microcontrollers and registering their authentication token on the server.
"""

__author__ = "Moritz Ulmer"
__license__ = "apache-2.0"
__version__ = "0.2.1"
__date__ = "21.03.2022"
__maintainer__ = "Moritz Ulmer"
__email__ = "moritz@silentwind.eu "
__status__ = "Development"

import argparse
import logging
import os
import platform
import sys

# Change the current dir to the temporary one created by PyInstaller
try:
    os.chdir(sys._MEIPASS)
except:
    pass

# Needed for Wayland applications
if platform.system() == "posix":
    os.environ["QT_QPA_PLATFORM"] = "xcb"

import ctypes
from PySide6 import QtCore
from PySide6.QtWidgets import QApplication

from config import Config
from controller import Controller
from flash_model import FlashModel
from main_view import MainView
from server_model import ServerModel
from wifi_model import WiFiModel


def main():
    # Required on Windows to use own app icon
    if platform.system() == "Windows":
        myappid = f"inamata.co.flasher.{__version__}"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v", "--verbose", help="increase output verbosity", action="store_true"
    )
    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.DEBUG)
    else:
        logging.basicConfig(format="%(levelname)s: %(message)s")

    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts)
    inamata_flasher = QApplication(sys.argv)

    view = MainView(__version__)
    config = Config()
    server_model = ServerModel(config=config)
    flash_model = FlashModel(server_model=server_model, config=config)
    wifi_model = WiFiModel(config=config)
    controller = Controller(
        server_model=server_model,
        flash_model=flash_model,
        wifi_model=wifi_model,
        view=view,
        config=config,
    )
    view.show()
    sys.exit(inamata_flasher.exec())


if __name__ == "__main__":
    main()
