from flash_model import FlashModel
import os
import sys
import logging
import argparse

# Needed for Wayland applications
os.environ["QT_QPA_PLATFORM"] = "xcb"
# Change the current dir to the temporary one created by PyInstaller
try:
    os.chdir(sys._MEIPASS)
except:
    pass

from PySide2.QtWidgets import QApplication
from PySide2 import QtCore

from config import Config
from controller import Controller
from server_model import ServerModel
from main_view import MainView
from wifi_model import WiFiModel


def main():
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
    ds_flasher = QApplication(sys.argv)
    # Enable High DPI display with PyQt5
    if hasattr(QtCore.Qt, "AA_UseHighDpiPixmaps"):
        ds_flasher.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps)
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
    sys.exit(ds_flasher.exec_())


if __name__ == "__main__":
    main()
