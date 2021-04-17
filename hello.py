import os
import sys

### Settings
ui_file_name = "mainwindow.ui"

# Needed for Wayland applications
os.environ["QT_QPA_PLATFORM"] = "xcb"
# Change the current dir to the temporary one created by PyInstaller
try:
    os.chdir(sys._MEIPASS)
    print(sys._MEIPASS)
except:
    pass

from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QApplication, QMainWindow
from PySide2.QtCore import QFile, QIODevice

class DSFlasherModel:
    def login(self):
        print("Logging in...")
    
    def sign_up(self):
        print("Signing up!")

class DSFlasherUi(QMainWindow):
    def __init__(self):
        super().__init__()
        ui_file = QFile(ui_file_name)
        if not ui_file.open(QIODevice.ReadOnly):
            print(f"Cannot open {ui_file_name}: {ui_file.errorString()}")
            sys.exit(-1)
        self.ui = QUiLoader().load(ui_file)
        ui_file.close()
    
    def show(self):
        self.ui.show()

class DSFlasherCtrl:
    def __init__(self, model, view):
        self._model = model
        self._view = view
        self._connectSignals()
    
    def _connectSignals(self):
        self._view.ui.loginButton.clicked.connect(self._model.login)
        self._view.ui.signUpButton.clicked.connect(self._model.sign_up)

def main():
    ds_flasher = QApplication(sys.argv)
    view = DSFlasherUi()
    view.show()
    model = DSFlasherModel
    DSFlasherCtrl(model=model, view=view)
    sys.exit(ds_flasher.exec_())

if __name__ == "__main__":
    main()
