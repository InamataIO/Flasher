import sys
from typing import Callable

from PySide6.QtCore import QCoreApplication, QFile, QIODevice
from PySide6.QtGui import QCloseEvent
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QWidget

from config import Config
from main_view import MainView


class AboutView(QWidget):
    """Window to display licenses and about info."""

    def __init__(self, main_view: MainView, config: Config):
        super().__init__()

        self._config = config
        self._main_view = main_view
        ui_path = self._config.uis_folder / "about.ui"
        ui_file = QFile(str(ui_path))
        if not ui_file.open(QIODevice.ReadOnly):
            print(f"Cannot open {ui_path}: {ui_file.errorString()}")
            sys.exit(-1)
        self.ui = QUiLoader().load(ui_file, self)
        ui_file.close()
        self.ui.setFont(main_view.font())
        self.ui.setWindowIcon(main_view.windowIcon())
        self.ui.setWindowTitle(self.about_label())
        self.ui.setContentsMargins(8, 8, 8, 8)
        self.ui.closeButton.clicked.connect(self.close)
        self.close_callback: Callable[[QCloseEvent], None] = None

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.close_callback:
            self.close_callback(event)
        else:
            event.accept()

    @staticmethod
    def about_label() -> str:
        return QCoreApplication.translate("main", "About")
