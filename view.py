from functools import partial
import sys

from PySide2.QtCore import QFile, QIODevice
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QMainWindow, QMessageBox


### Settings
main_window_file = "mainwindow.ui"
page_2_file = "page2.ui"

class DSFlasherUi(QMainWindow):
    def __init__(self):
        super().__init__()
        ui_file = QFile(main_window_file)
        if not ui_file.open(QIODevice.ReadOnly):
            print(f"Cannot open {main_window_file}: {ui_file.errorString()}")
            sys.exit(-1)
        self.ui = QUiLoader().load(ui_file)
        ui_file.close()
        go_back = partial(self.ui.stackedWidget.setCurrentIndex, 0)
        self.ui.pushButton.clicked.connect(go_back)

    def notify(self, message, title, level="information"):
        if level == "information":
            QMessageBox.information(self.ui, title, message)
        if level == "warning":
            QMessageBox.warning(self.ui, title, message)
        if level == "critical":
            QMessageBox.critical(self.ui, title, message)


    def show(self):
        self.ui.show()

    def switch(self):
        print("ho")
        self.ui.stackedWidget.setCurrentIndex(1)
        
