from functools import partial
import sys
from typing import Any, Dict, List, Union

from PySide2.QtCore import QFile, QIODevice
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QMainWindow, QMessageBox, QWidget


### Settings
main_window_file = "mainwindow.ui"
page_2_file = "page2.ui"


class DSFlasherUi(QMainWindow):
    class Pages:
        LOGIN = ["loginPage", -1]
        WELCOME = ["welcomePage", -1]
        REPLACE_CONTROLLER = ["replaceControllerPage", -1]
        ADD_CONTROLLER = ["addControllerPage", -1]
        ADD_WIFI = ["addWiFiPage", -1]
        MANAGE_WIFI = ["manageWiFiPage", -1]

        @classmethod
        def all(cls) -> List:
            return [value for name, value in vars(cls).items() if name.isupper()]

    def __init__(self):
        super().__init__()
        ui_file = QFile(main_window_file)
        if not ui_file.open(QIODevice.ReadOnly):
            print(f"Cannot open {main_window_file}: {ui_file.errorString()}")
            sys.exit(-1)
        self.ui = QUiLoader().load(ui_file)
        ui_file.close()
        self._set_page_indexes()

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

    def change_page(self, page: Union[str, List]):
        """Change the stack page to the specified page"""
        if isinstance(page, str):
            # Search for the page widget by name and use the index set during init
            index = next([i[1] for i in self.Pages.all() if i[0] == page])
        else:
            index = page[1]
        self.ui.stackedWidget.setCurrentIndex(index)

    def _set_page_indexes(self):
        """Find the indexes for the named pages in the stacked widget."""
        for i in self.Pages.all():
            page = self.ui.findChild(QWidget, i[0])
            index = self.ui.stackedWidget.indexOf(page)
            i[1] = index