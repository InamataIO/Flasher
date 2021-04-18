import os
import sys

# Needed for Wayland applications
os.environ["QT_QPA_PLATFORM"] = "xcb"
# Change the current dir to the temporary one created by PyInstaller
try:
    os.chdir(sys._MEIPASS)
except:
    pass

from PySide2.QtWidgets import QApplication
from PySide2 import QtCore

from model import DSFlasherModel
from controller import DSFlasherCtrl
from view import DSFlasherUi


def main():
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts)
    ds_flasher = QApplication(sys.argv)
    # Enable High DPI display with PyQt5
    if hasattr(QtCore.Qt, 'AA_UseHighDpiPixmaps'):
        ds_flasher.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps)
    view = DSFlasherUi()
    view.show()
    model = DSFlasherModel()
    DSFlasherCtrl(model=model, view=view)
    sys.exit(ds_flasher.exec_())

if __name__ == "__main__":
    main()
