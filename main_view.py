import sys
from typing import Callable, List, Union

from PySide2.QtCore import QEvent, QFile, QIODevice, QSize
from PySide2.QtGui import QCloseEvent, QIcon, QFontDatabase, QFont
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QMainWindow, QMessageBox, QWidget

### Settings
main_window_file = "mainwindow.ui"
page_2_file = "page2.ui"


class MainView(QMainWindow):
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

    close_callback: Callable[[QCloseEvent], None] = None

    def __init__(self, version: str):
        super().__init__()
        ui_file = QFile(main_window_file)
        if not ui_file.open(QIODevice.ReadOnly):
            print(f"Cannot open {main_window_file}: {ui_file.errorString()}")
            sys.exit(-1)
        self.ui = QUiLoader().load(ui_file)
        ui_file.close()
        self.ui.welcomeVersion.setText(version)
        self.setCentralWidget(self.ui)
        self.setWindowTitle("Togayo Flasher")
        self._set_font()
        self._set_page_indexes()
        self._hide_disabled_widgets()
        self._add_app_icon()

    def notify(self, message, title, level="information"):
        if level == "information":
            QMessageBox.information(self.ui, title, message)
        if level == "warning":
            QMessageBox.warning(self.ui, title, message)
        if level == "critical":
            QMessageBox.critical(self.ui, title, message)

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

    def _set_font(self):
        """Set the font used by the UI."""
        id = QFontDatabase.addApplicationFont("./fonts/Lato-Regular.ttf")
        _fontstr = QFontDatabase.applicationFontFamilies(id)[0]
        _font = QFont(_fontstr, 16)
        self.setFont(_font)

    def _hide_disabled_widgets(self):
        """Preemptively hide disabled widgets."""
        self.ui.manageWiFiEditButton.hide()
        self.ui.loginLoadingText.hide()
        self.ui.loginLoadingBar.hide()
        self.ui.addControllerLoadingText.hide()
        self.ui.addControllerLoadingBar.hide()
        self.ui.addControllerProgressText.hide()
        self.ui.addControllerProgressBar.hide()
        self.ui.replaceControllerLoadingText.hide()
        self.ui.replaceControllerLoadingBar.hide()
        self.ui.replaceControllerProgressText.hide()
        self.ui.replaceControllerProgressBar.hide()

    def _add_app_icon(self):
        """Add a window app icon that is also used in the task bar."""
        app_icon = QIcon()
        app_icon.addFile("images/icon_512.png", QSize(512, 512))
        app_icon.addFile("images/icon_256.png", QSize(256, 256))
        app_icon.addFile("images/icon_128.png", QSize(128, 128))
        app_icon.addFile("images/icon_64.png", QSize(64, 64))
        app_icon.addFile("images/icon_32.png", QSize(32, 32))
        app_icon.addFile("images/icon_16.png", QSize(16, 16))
        self.setWindowIcon(app_icon)

    def eventFilter(self, watched, event):
        """Catch the close event to save settings."""
        if watched is self.ui and event.type() == QEvent.Close:
            self.closeEvent(event)
        return super().eventFilter(watched, event)

    def closeEvent(self, event):
        """Pass the close event to the registered close callback."""
        if self.close_callback:
            self.close_callback(event)
        else:
            event.accept()
