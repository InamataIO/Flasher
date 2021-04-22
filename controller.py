from config import DSFlasherConfig
from functools import partial

from PySide2.QtCore import QThreadPool
from PySide2.QtGui import QCloseEvent

from model import DSFlasherModel
from view import DSFlasherUi
from wifi_model import DSFlasherWiFiModel
from worker import Worker, WorkerInformation, WorkerWarning


class DSFlasherCtrl:
    def __init__(
        self,
        model: DSFlasherModel,
        view: DSFlasherUi,
        wifi_model: DSFlasherWiFiModel,
        config: DSFlasherConfig,
    ):
        self._model = model
        self._view = view
        self._wifi_model = wifi_model
        self._config = config

        self.threadpool = QThreadPool()
        self._connect_signals()
        self._connect_model_views()
        self._page_after_add_wifi = None
        self._page_before_add_wifi = None
        if model.is_authenticated():
            view.change_page(view.Pages.WELCOME)
        else:
            view.change_page(view.Pages.LOGIN)

    def _connect_signals(self):
        # Main Application
        self._view.close_callback = self.handle_close

        # Login Page
        self._view.ui.loginButton.clicked.connect(self.log_in)
        self._view.ui.signUpButton.clicked.connect(self._model.sign_up)
        self._view.ui.emailLineEdit.setText(self._model.get_username())
        self._view.ui.emailLineEdit.returnPressed.connect(
            self._view.ui.loginButton.click
        )
        self._view.ui.passwordLineEdit.returnPressed.connect(
            self._view.ui.loginButton.click
        )

        # Welcome Page
        self._view.ui.welcomeAddControllerButton.clicked.connect(self.add_controller)
        self._view.ui.welcomeReplaceControllerButton.clicked.connect(
            self.replace_controller
        )
        self._view.ui.welcomeManageWiFiButton.clicked.connect(self.manage_wifi)
        self._view.ui.welcomeLogOutPushButton.clicked.connect(self.log_out)
        self._view.ui.welcomeUsername.setText(self._model.get_username())

        # Add Controller Page
        self._view.ui.addControllerFlashButton.clicked.connect(self.download_and_flash)
        self._view.ui.addBackPushButton.clicked.connect(self.to_welcome_page)

        # Replace Controller Page
        self._view.ui.replaceBackPushButton.clicked.connect(self.to_welcome_page)

        # Add WiFi Page
        self._view.ui.addWiFiSubmitPushButton.clicked.connect(self.add_wifi_ap)
        self._view.ui.addWiFiBackPushButton.clicked.connect(self.back_from_add_wifi)

        # Manage WiFi Page
        self._view.ui.manageWiFiAddButton.clicked.connect(self.manage_wifi_to_add_wifi)
        self._view.ui.manageWiFiRemoveButton.clicked.connect(self.remove_wifi_ap)
        self._view.ui.manageWiFiBackButton.clicked.connect(self.to_welcome_page)

    def _connect_model_views(self):
        self._view.ui.apListView.setModel(self._wifi_model)
        self._view.ui.addControllerAPListView.setModel(self._wifi_model)

    def log_out(self):
        self._model.log_out()
        self._view.ui.passwordLineEdit.clear()
        self._view.change_page(self._view.Pages.LOGIN)

    def log_in(self):
        email = self._view.ui.emailLineEdit.text()
        password = self._view.ui.passwordLineEdit.text()
        worker = Worker(self._model.log_in, email, password)
        worker.signals.result.connect(self.log_in_result)
        worker.signals.error.connect(self.handle_error)
        self.threadpool.start(worker)

    def log_in_result(self, _):
        email = self._view.ui.emailLineEdit.text()
        self._view.ui.welcomeUsername.setText(email)
        self._view.change_page(self._view.Pages.WELCOME)
        self._view.ui.passwordLineEdit.clear()

    def handle_error(self, error):
        if isinstance(error, WorkerInformation):
            self._view.notify(str(error), "", "information")
        elif isinstance(error, WorkerWarning):
            self._view.notify(str(error), "", "warning")
        else:
            self._view.notify(str(error), "", "critical")

    def add_controller(self):
        if self._wifi_model.ap_count():
            self._view.change_page(self._view.Pages.ADD_CONTROLLER)
        else:
            self._page_after_add_wifi = self._view.Pages.ADD_CONTROLLER
            self._view.change_page(self._view.Pages.ADD_WIFI)

    def replace_controller(self):
        if self._wifi_model.ap_count():
            self._view.change_page(self._view.Pages.REPLACE_CONTROLLER)
        else:
            self._page_after_add_wifi = self._view.Pages.REPLACE_CONTROLLER
            self._view.change_page(self._view.Pages.ADD_WIFI)

    def manage_wifi(self):
        if self._wifi_model.ap_count():
            self._view.change_page(self._view.Pages.MANAGE_WIFI)
        else:
            self._page_after_add_wifi = self._view.Pages.MANAGE_WIFI
            self._view.change_page(self._view.Pages.ADD_WIFI)

    def download_and_flash(self):
        self._view.ui.addControllerProgressText.show()
        self._view.ui.addControllerProgressBar.show()

    def add_wifi_ap(self):
        """Add the WiFi AP according to the user input (SSID, password)."""
        ssid = self._view.ui.addWiFiSSIDLineEdit.text()
        password = self._view.ui.addWiFiPasswordLineEdit.text()
        self._wifi_model.add_ap(ssid, password)
        self._view.change_page(self._page_after_add_wifi)
        self._view.ui.addWiFiSSIDLineEdit.clear()
        self._view.ui.addWiFiPasswordLineEdit.clear()

    def back_from_add_wifi(self):
        """Go to the previous page"""
        if self._page_before_add_wifi:
            self._view.change_page(self._page_before_add_wifi)
            self._page_before_add_wifi = None

    def manage_wifi_to_add_wifi(self):
        self._page_before_add_wifi = self._view.Pages.MANAGE_WIFI
        self._page_after_add_wifi = self._view.Pages.MANAGE_WIFI
        self._view.change_page(self._view.Pages.ADD_WIFI)

    def remove_wifi_ap(self):
        """Remove the currently selected WiFi AP."""
        if indexes := self._view.ui.apListView.selectedIndexes():
            self._wifi_model.remove_ap(indexes[0].row())

    def to_welcome_page(self):
        """Switch to the welcome page."""
        self._view.change_page(self._view.Pages.WELCOME)

    def handle_close(self, event: QCloseEvent):
        """Save the config on close."""
        self._wifi_model.save_to_config()
        self._config.save_config()
        event.accept()
