import sys
from typing import Callable

from PySide6.QtCore import QCoreApplication, QFile, QIODevice
from PySide6.QtGui import QCloseEvent, QPixmap
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QMessageBox, QWidget

from config import Config
from main_view import MainView


class SerialMonitorView(QWidget):
    """Window to display the serial monitor."""

    def __init__(self, main_view: MainView, config: Config):
        super().__init__()
        self._config = config
        self._main_view = main_view

        ui_path = self._config.uis_folder / "serial_monitor.ui"
        ui_file = QFile(str(ui_path))
        if not ui_file.open(QIODevice.ReadOnly):
            print(f"Cannot open {ui_path}: {ui_file.errorString()}")
            sys.exit(-1)
        self.ui = QUiLoader().load(ui_file, self)
        ui_file.close()
        self.ui.setFont(main_view.font())
        self.ui.setWindowIcon(main_view.windowIcon())
        self.ui.setWindowTitle(self.serial_monitor_label())
        self.ui.setContentsMargins(8, 8, 8, 8)
        self.close_callback: Callable[[QCloseEvent], None] = None
        self._set_button_icons()

    def _set_button_icons(self) -> None:
        folder = self._config.images_folder
        self.play_icon = QPixmap(str(folder / "play_icon.png"))
        self.pause_icon = QPixmap(str(folder / "pause_icon.png"))
        self.ui.startStopButton.setIcon(self.play_icon)
        update_icon = QPixmap(str(folder / "update_icon.png"))
        self.ui.updateComButton.setIcon(update_icon)
        self.ui.baudRateComboBox.hide()
        self.ui.encodingComboBox.hide()

    def set_start_stop_icon(self, started: bool) -> None:
        if started:
            self.ui.startStopButton.setIcon(self.pause_icon)
        else:
            self.ui.startStopButton.setIcon(self.play_icon)

    def notify(self, message, title, level="information"):
        if level == "information":
            QMessageBox.information(self.ui, title, message)
        if level == "warning":
            QMessageBox.warning(self.ui, title, message)
        if level == "critical":
            QMessageBox.critical(self.ui, title, message)

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.close_callback:
            self.close_callback(event)
        else:
            event.accept()

    def serial_monitor_label(self) -> str:
        return QCoreApplication.translate("serial", "Serial Monitor")
