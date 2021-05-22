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
from PySide2 import QtCore
from PySide2.QtWidgets import QApplication, QStyleFactory
from PySide2.QtGui import QIcon

from config import Config
from controller import Controller
from flash_model import FlashModel
from main_view import MainView
from server_model import ServerModel
from wifi_model import WiFiModel


def main():
    # Required on Windows to use own app icon
    if platform.system() == "Windows":
        myappid = 'togayo.com.flasher.0.0.1' # arbitrary string
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
    togayo_flasher = QApplication(sys.argv)
    togayo_flasher.setStyle(QStyleFactory.create("Fusion"))

    # Enable High DPI display with PyQt5
    if hasattr(QtCore.Qt, "AA_UseHighDpiPixmaps"):
        togayo_flasher.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps)
    view = MainView()
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
    sys.exit(togayo_flasher.exec_())


if __name__ == "__main__":
    main()
