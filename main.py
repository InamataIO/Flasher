import os
import sys
import io
from contextlib import redirect_stdout
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

# import esptool

from config import DSFlasherConfig
from controller import DSFlasherCtrl
from model import DSFlasherModel
from view import DSFlasherUi
from wifi_model import DSFlasherWiFiModel


# f = io.StringIO()
# try:
#     with redirect_stdout(f):
#         print('foobar')
#         esptool.main(["read_mac"])
#         print(12)
# except esptool.FatalError as err:
#     print(err)
# except esptool.UnsupportedCommandError as err:
#     print(err)
# print('Got stdout: "{0}"'.format(f.getvalue()))
# exit()


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
    view = DSFlasherUi()
    config = DSFlasherConfig()
    model = DSFlasherModel(config=config)
    wifi_model = DSFlasherWiFiModel(config=config)
    controller = DSFlasherCtrl(
        model=model, view=view, wifi_model=wifi_model, config=config
    )
    view.show()
    sys.exit(ds_flasher.exec_())


if __name__ == "__main__":
    main()
