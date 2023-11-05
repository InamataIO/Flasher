import sys

from PySide6.QtCore import QCoreApplication, QFile, QIODevice
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QDialog

from config import Config
from main_view import MainView


class AboutView(QDialog):
    """Window to display licenses and about info."""

    def __init__(self, main_view: MainView, config: Config):
        super().__init__(main_view)

        self._config = config
        self._main_view = main_view
        ui_path = self._config.uis_folder / "about.ui"
        ui_file = QFile(str(ui_path))
        if not ui_file.open(QIODevice.ReadOnly):
            print(f"Cannot open {ui_path}: {ui_file.errorString()}")
            sys.exit(-1)
        self.ui = QUiLoader().load(ui_file)
        ui_file.close()
        self.ui.setFont(main_view.font())
        self.ui.setWindowIcon(main_view.windowIcon())
        self.ui.setWindowTitle(self.about_label())
        self.ui.closeButton.clicked.connect(self.ui.close)

    def show(self):
        self.ui.show()

    @staticmethod
    def about_label() -> str:
        return QCoreApplication.translate("main", "About")
