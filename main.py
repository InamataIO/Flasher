import os
import sys
import io
from contextlib import redirect_stdout

# Needed for Wayland applications
os.environ["QT_QPA_PLATFORM"] = "xcb"
# Change the current dir to the temporary one created by PyInstaller
try:
    os.chdir(sys._MEIPASS)
except:
    pass

from PySide2.QtWidgets import QApplication
from PySide2 import QtCore
import esptool

from model import DSFlasherModel
from controller import DSFlasherCtrl
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
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts)
    ds_flasher = QApplication(sys.argv)
    # Enable High DPI display with PyQt5
    if hasattr(QtCore.Qt, 'AA_UseHighDpiPixmaps'):
        ds_flasher.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps)
    view = DSFlasherUi()
    view.show()
    model = DSFlasherModel()
    aps = [(False, 'an item'), (False, 'another item')]
    wifi_model = DSFlasherWiFiModel(aps=aps)
    controller = DSFlasherCtrl(model=model, view=view, wifi_model=wifi_model)
    sys.exit(ds_flasher.exec_())

if __name__ == "__main__":
    main()
