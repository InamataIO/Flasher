import sys
from enum import Enum
from typing import Callable, List, Union

from PySide6.QtCore import QEvent, QFile, QIODevice, QSize
from PySide6.QtGui import QCloseEvent, QFont, QFontDatabase, QIcon, QPixmap
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QMainWindow, QMessageBox, QWidget

from config import Config


class MainView(QMainWindow):
    class Pages(Enum):
        LOGIN = ["loginPage", -1]
        WELCOME = ["welcomePage", -1]
        REPLACE_CONTROLLER = ["replaceControllerPage", -1]
        ADD_CONTROLLER = ["addControllerPage", -1]
        ADD_WIFI = ["addWiFiPage", -1]
        UPDATE_WIFI = ["updateWiFiPage", -1]
        MANAGE_WIFI = ["manageWiFiPage", -1]
        SYSTEM_SETTINGS = ["systemSettingsPage", -1]

        @classmethod
        def all(cls) -> List:
            return [value for name, value in vars(cls).items() if name.isupper()]

    close_callback: Callable[[QCloseEvent], None] = None

    def __init__(self, config: Config):
        super().__init__()

        self._config = config
        ui_path = self._config.uis_folder / "mainwindow.ui"
        ui_file = QFile(str(ui_path))
        if not ui_file.open(QIODevice.ReadOnly):
            print(f"Cannot open {ui_path}: {ui_file.errorString()}")
            sys.exit(-1)
        self.ui = QUiLoader().load(ui_file)
        ui_file.close()
        self.ui.welcomeVersionButton.setText(config.app_version)
        self.ui.loginVersionButton.setText(config.app_version)
        self.setCentralWidget(self.ui)
        self.setWindowTitle("Inamata Flasher")
        self._set_font()
        self._set_page_indexes()
        self._hide_disabled_widgets()
        self._add_app_icon()
        self._set_button_icons()
        self.original_login_link_text = self.ui.loginLinkText.text()

    def notify(self, message, title, level="information"):
        if level == "information":
            QMessageBox.information(self.ui, title, message)
        if level == "warning":
            QMessageBox.warning(self.ui, title, message)
        if level == "critical":
            QMessageBox.critical(self.ui, title, message)

    def change_page(self, page: Union[str, List]):
        """Change the stack page to the specified page."""
        if isinstance(page, str):
            # Search for the page widget by name and use the index set during init
            index = next([i.value[1] for i in self.Pages if i.value[0] == page])
        else:
            index = page.value[1]
        self.ui.stackedWidget.setCurrentIndex(index)

    def current_page(self) -> Pages | None:
        """Return the current page."""
        try:
            return next(
                i
                for i in self.Pages
                if self.ui.stackedWidget.currentIndex() == i.value[1]
            )
        except StopIteration:
            return None

    def _set_page_indexes(self):
        """Find the indexes for the named pages in the stacked widget."""
        for i in self.Pages:
            page = self.ui.findChild(QWidget, i.value[0])
            index = self.ui.stackedWidget.indexOf(page)
            i.value[1] = index

    def _set_font(self):
        """Set the font used by the UI."""
        font_file = self._config.fonts_folder / "Roboto_Regular.ttf"
        font_id = QFontDatabase.addApplicationFont(str(font_file))
        _fontstr = QFontDatabase.applicationFontFamilies(font_id)[0]
        _font = QFont(_fontstr, 16)
        self.setFont(_font)

    def _hide_disabled_widgets(self):
        """Preemptively hide disabled widgets."""
        self.ui.loginLoadingText.hide()
        self.ui.loginLoadingBar.hide()
        self.ui.loginLinkText.hide()
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
        folder = self._config.images_folder
        app_icon = QIcon()
        app_icon.addFile(str(folder / "icon_512.png"), QSize(512, 512))
        app_icon.addFile(str(folder / "icon_256.png"), QSize(256, 256))
        app_icon.addFile(str(folder / "icon_128.png"), QSize(128, 128))
        app_icon.addFile(str(folder / "icon_64.png"), QSize(64, 64))
        app_icon.addFile(str(folder / "icon_32.png"), QSize(32, 32))
        app_icon.addFile(str(folder / "icon_16.png"), QSize(16, 16))
        self.setWindowIcon(app_icon)

    def _set_button_icons(self):
        """For Windows, use custom button icons."""
        pixmap = QPixmap(str(self._config.images_folder / "inamata_flasher_logo.png"))
        self.ui.loginLogo.setPixmap(pixmap)

        folder = self._config.images_folder
        settings_icon = QPixmap(str(folder / "setting_line_icon.png"))
        self.ui.loginSystemIconButton.setIcon(settings_icon)
        help_icon = QPixmap(str(folder / "question_mark_line_icon.png"))
        self.ui.loginHelpIconButton.setIcon(help_icon)
        self.ui.welcomeHelpIconButton.setIcon(help_icon)
        locale_icon = QPixmap(str(folder / "locale_icon.png"))
        self.ui.loginLocaleIconButton.setIcon(locale_icon)
        self.ui.welcomeLocaleIconButton.setIcon(locale_icon)

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
