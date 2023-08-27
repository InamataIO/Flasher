#!/usr/bin/env python

"""Register ESP32's with the Inamata Server

Inamata Flasher is a tool for flashing the Inamata controller firmware on ESP32
microcontrollers and registering their authentication token on the server.
"""

import os
import sys

# Change the current dir to the temporary one created by PyInstaller
try:
    os.chdir(sys._MEIPASS)
except AttributeError:
    pass

import argparse
import ctypes
import logging
import platform

from PySide6 import QtCore
from PySide6.QtWidgets import QApplication

from config import Config
from controller import Controller
from flash_model import FlashModel
from main_view import MainView
from server_model import ServerModel
from wifi_model import WiFiModel

__version__ = "0.4.9"


def main():
    # Required on Windows to use own app icon
    if platform.system() == "Windows":
        myappid = f"inamata.co.flasher.{__version__}"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v", "--verbose", help="increase output verbosity", action="store_true"
    )
    parser.add_argument("-d", "--debug", help="start debugpy", action="store_true")
    args = parser.parse_args()
    log_level = logging.INFO if not args.verbose else logging.DEBUG
    logging.basicConfig(
        format="%(levelname)s | %(name)s.%(funcName)s:%(lineno)s | %(message)s",
        level=log_level,
    )
    if args.debug:
        import debugpy

        debugpy.listen(5678)

    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts)
    inamata_flasher = QApplication(sys.argv)

    config = Config()
    view = MainView(version=__version__, config=config)
    server_model = ServerModel(config=config)
    flash_model = FlashModel(server_model=server_model, config=config)
    wifi_model = WiFiModel(config=config)
    controller = Controller(
        server_model=server_model,
        flash_model=flash_model,
        wifi_model=wifi_model,
        view=view,
        config=config,
        app=inamata_flasher,
    )
    view.show()
    sys.exit(inamata_flasher.exec())


if __name__ == "__main__":
    main()
