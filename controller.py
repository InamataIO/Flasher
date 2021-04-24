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
        """Connect widget signals to the appropriate function."""
        # Main Application
        self._view.close_callback = self.handle_close
        self._view.ui.stackedWidget.currentChanged.connect(self.page_changed)

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
        self._view.ui.welcomeAddControllerButton.clicked.connect(self.to_add_controller)
        self._view.ui.welcomeReplaceControllerButton.clicked.connect(
            self.replace_controller
        )
        self._view.ui.welcomeManageWiFiButton.clicked.connect(self.manage_wifi)
        self._view.ui.welcomeLogOutPushButton.clicked.connect(self.log_out)
        self._view.ui.welcomeUsername.setText(self._model.get_username())

        # Add Controller Page
        self._view.ui.addControllerFlashButton.clicked.connect(self.download_and_flash)
        self._view.ui.addControllerReloadButton.clicked.connect(
            self.add_controller_reload
        )
        self._view.ui.addBackPushButton.clicked.connect(self.to_welcome_page)

        # Replace Controller Page
        self._view.ui.replaceControllerSitesComboBox.currentIndexChanged.connect(
            self.replace_controller_site_selected
        )
        self._view.ui.replaceControllerReloadButton.clicked.connect(
            self.replace_controller_reload
        )
        self._view.ui.replaceBackPushButton.clicked.connect(self.to_welcome_page)

        # Add WiFi Page
        self._view.ui.addWiFiSubmitPushButton.clicked.connect(self.add_wifi_ap)
        self._view.ui.addWiFiBackPushButton.clicked.connect(self.back_from_add_wifi)

        # Manage WiFi Page
        self._view.ui.manageWiFiAddButton.clicked.connect(self.manage_wifi_to_add_wifi)
        self._view.ui.manageWiFiRemoveButton.clicked.connect(self.remove_wifi_ap)
        self._view.ui.manageWiFiBackButton.clicked.connect(self.to_welcome_page)

    def _connect_model_views(self):
        """Connect models to the appropriate views."""
        self._view.ui.apListView.setModel(self._wifi_model)
        self._view.ui.addControllerAPListView.setModel(self._wifi_model)
        self._view.ui.replaceControllerAPListView.setModel(self._wifi_model)

    def log_out(self):
        """Log the user out and clear the password and auth token."""
        self._model.log_out()
        self._view.ui.passwordLineEdit.clear()
        self._view.change_page(self._view.Pages.LOGIN)

    def log_in(self):
        """Log the user in and save the auth token."""
        self._view.ui.loginLoadingText.show()
        self._view.ui.loginLoadingBar.show()
        email = self._view.ui.emailLineEdit.text()
        password = self._view.ui.passwordLineEdit.text()
        worker = Worker(self._model.log_in, email, password)
        worker.signals.result.connect(self.log_in_result)
        worker.signals.error.connect(self.log_in_error)
        worker.signals.finished.connect(self.log_in_finished)
        self.threadpool.start(worker)

    def log_in_result(self, _):
        """If login succeeds, go to the welcome page."""
        email = self._view.ui.emailLineEdit.text()
        self._view.ui.welcomeUsername.setText(email)
        self._view.change_page(self._view.Pages.WELCOME)
        self._view.ui.passwordLineEdit.clear()

    def log_in_finished(self):
        """After the login attempt, hide the loading widgets."""
        self._view.ui.loginLoadingText.hide()
        self._view.ui.loginLoadingBar.hide()

    def handle_error(self, error):
        """
        Handle errors raised by worker threads. Error handler. Use separate callbacks below to
        avoid double free segmentation error.
        """
        if isinstance(error, WorkerInformation):
            self._view.notify(str(error), "", "information")
        elif isinstance(error, WorkerWarning):
            self._view.notify(str(error), "", "warning")
        else:
            self._view.notify(str(error), "", "critical")

    def log_in_error(self, error):
        """Error handler for the login thread."""
        self.handle_error(error)

    def handle_add_controller_page_error(self, error):
        """Error handler for the add controller data fetch thread."""
        self.handle_error(error)

    def handle_replace_controller_page_error(self, error):
        """Error handler for the replace controller data fetch thread."""
        self.handle_error(error)

    def replace_controller_load_controllers_error(self, error):
        """Error handler for fetching the controllers thread."""
        self.handle_error(error)

    def to_add_controller(self):
        """Request to switch to the add controller page. Go to add wifi if none exist."""
        if self._wifi_model.ap_count():
            self._view.change_page(self._view.Pages.ADD_CONTROLLER)
        else:
            self._page_after_add_wifi = self._view.Pages.ADD_CONTROLLER
            self._view.change_page(self._view.Pages.ADD_WIFI)

    def replace_controller(self):
        """Request to switch to the replace controller page. Go to add wifi if none exist."""
        if self._wifi_model.ap_count():
            self._view.change_page(self._view.Pages.REPLACE_CONTROLLER)
        else:
            self._page_after_add_wifi = self._view.Pages.REPLACE_CONTROLLER
            self._view.change_page(self._view.Pages.ADD_WIFI)

    def manage_wifi(self):
        """Request to switch to the mange page. Go to add wifi if none exist."""
        if self._wifi_model.ap_count():
            self._view.change_page(self._view.Pages.MANAGE_WIFI)
        else:
            self._page_after_add_wifi = self._view.Pages.MANAGE_WIFI
            self._view.change_page(self._view.Pages.ADD_WIFI)

    def download_and_flash(self):
        """Download the selected firmware image and flash it to the ESP."""
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

    def page_changed(self, index: int):
        """Called when the page of the stacked widget changes"""
        if index == self._view.Pages.LOGIN[1]:
            pass
        elif index == self._view.Pages.WELCOME[1]:
            pass
        elif index == self._view.Pages.ADD_CONTROLLER[1]:
            self.handle_add_controller_page()
        elif index == self._view.Pages.REPLACE_CONTROLLER[1]:
            self.handle_replace_controller_page()
        else:
            pass

    def handle_add_controller_page(self):
        """Get data and populate the combo boxes on the add controller page."""
        if self._config.config.get("sites"):
            self.handle_add_controller_page_result(None)
        else:
            self._view.ui.addControllerLoadingText.show()
            self._view.ui.addControllerLoadingBar.show()
            worker = Worker(self._model.get_site_and_firmware_data)
            worker.signals.result.connect(self.handle_add_controller_page_result)
            worker.signals.error.connect(self.handle_add_controller_page_error)
            worker.signals.finished.connect(self.handle_add_controller_page_finished)
            self.threadpool.start(worker)

    def handle_add_controller_page_result(self, _):
        """Populate the combo boxes with the fetched data for the add controller page."""
        # Update the site combo box and retain the currently selected item
        current_site = self._view.ui.addControllerSitesComboBox.currentData()
        self._view.ui.addControllerSitesComboBox.clear()
        for i in self._config.config.get("sites", []):
            self._view.ui.addControllerSitesComboBox.addItem(
                i["name"], userData=i["id"]
            )
        if current_site:
            index = self._view.ui.addControllerSitesComboBox.findData(current_site)
            if index:
                self._view.ui.addControllerSitesComboBox.setCurrentIndex(index)

        # Update the firmware combo box and retain the currently selected item
        current_firmware = self._view.ui.addControllerFirmwaresComboBox.currentData()
        self._view.ui.addControllerFirmwaresComboBox.clear()
        for i in self._config.config.get("firmware_images", []):
            self._view.ui.addControllerFirmwaresComboBox.addItem(
                f"{i['name']} {i['version']}", userData=i["id"]
            )
        if current_firmware:
            index = self._view.ui.addControllerFirmwaresComboBox.findData(
                current_firmware
            )
            if index:
                self._view.ui.addControllerFirmwaresComboBox.setCurrentIndex(index)

    def handle_add_controller_page_finished(self):
        """Hide the loading widgets for the add controller page."""
        self._view.ui.addControllerLoadingText.hide()
        self._view.ui.addControllerLoadingBar.hide()

    def add_controller_reload(self):
        """Clear the cached data and repopulate the combo boxes."""
        self._config.clear_cached_data()
        self.handle_add_controller_page()

    def handle_replace_controller_page(self):
        """Fetch data and populate the combo boxes for the replace controller page."""
        if self._config.config.get("sites"):
            self.handle_replace_controller_page_result(None)
        else:
            self._view.ui.replaceControllerLoadingText.show()
            self._view.ui.replaceControllerLoadingBar.show()
            worker = Worker(self._model.get_site_and_firmware_data)
            worker.signals.result.connect(self.handle_replace_controller_page_result)
            worker.signals.error.connect(self.handle_replace_controller_page_error)
            worker.signals.finished.connect(
                self.handle_replace_controller_page_finished
            )
            self.threadpool.start(worker)

    def handle_replace_controller_page_result(self, _):
        """Populate the combo boxes excl. controllers for the replace controller page."""
        # Update the site combo box and retain the currently selected item
        # Block signals until setting the current index. Otherwise the controller combo box is
        # activated multiple times.
        current_site = self._view.ui.replaceControllerSitesComboBox.currentData()
        self._view.ui.replaceControllerSitesComboBox.clear()
        self._view.ui.replaceControllerSitesComboBox.blockSignals(True)
        for i in self._config.config.get("sites", []):
            self._view.ui.replaceControllerSitesComboBox.addItem(
                i["name"], userData=i["id"]
            )
        self._view.ui.replaceControllerSitesComboBox.blockSignals(False)
        index = self._view.ui.replaceControllerSitesComboBox.findData(current_site)
        if index >= 0:
            self._view.ui.replaceControllerSitesComboBox.setCurrentIndex(index)
        else:
            self._view.ui.replaceControllerSitesComboBox.currentIndexChanged.emit(0)
        # Update the firmware combo box and retain the currently selected item
        current_firmware = (
            self._view.ui.replaceControllerFirmwaresComboBox.currentData()
        )
        self._view.ui.replaceControllerFirmwaresComboBox.clear()
        for i in self._config.config.get("firmware_images", []):
            self._view.ui.replaceControllerFirmwaresComboBox.addItem(
                f"{i['name']} {i['version']}", userData=i["id"]
            )
        if current_firmware:
            index = self._view.ui.replaceControllerFirmwaresComboBox.findData(
                current_firmware
            )
            if index >= 0:
                self._view.ui.replaceControllerFirmwaresComboBox.setCurrentIndex(index)

    def handle_replace_controller_page_finished(self):
        """Hide the loading widgets for the replace controller page."""
        self._view.ui.replaceControllerLoadingText.hide()
        self._view.ui.replaceControllerLoadingBar.hide()

    def replace_controller_reload(self):
        """Clear cached data and repopulate the combo boxes on the replace controller page."""
        self._config.clear_cached_data()
        self.handle_replace_controller_page()

    def replace_controller_site_selected(self, index):
        """Start the process to populate the controller combo box for the selected site."""
        if site_id := self._view.ui.replaceControllerSitesComboBox.itemData(index):
            if site_id in self._config.config.get("controllers", {}):
                self.populate_replace_controller_controllers(site_id)
            else:
                self.replace_controller_load_controllers(site_id)

    def replace_controller_load_controllers(self, site_id):
        """Fetch available controllers for the selected site."""
        self._view.ui.replaceControllerLoadingText.show()
        self._view.ui.replaceControllerLoadingBar.show()
        worker = Worker(self._model.get_controller_data, site_id)
        worker.signals.result.connect(self.replace_controller_load_controllers_result)
        worker.signals.error.connect(self.replace_controller_load_controllers_error)
        worker.signals.finished.connect(
            self.replace_controller_load_controllers_finished
        )
        self.threadpool.start(worker)

    def replace_controller_load_controllers_result(self, _):
        """Populate the controller combo box with the fetched data."""
        site_id = self._view.ui.replaceControllerSitesComboBox.currentData()
        self.populate_replace_controller_controllers(site_id)

    def replace_controller_load_controllers_finished(self):
        """Hide the loading widgets on the replace controller page."""
        self._view.ui.replaceControllerLoadingText.hide()
        self._view.ui.replaceControllerLoadingBar.hide()

    def populate_replace_controller_controllers(self, site_id):
        """Populate the controller combo box for the selected site."""
        # Save the current item to restore the combo box selection later
        current_controller = (
            self._view.ui.replaceControllerControllersComboBox.currentData()
        )
        self._view.ui.replaceControllerControllersComboBox.clear()
        try:
            controllers = self._config.config["controllers"][site_id]
        except KeyError:
            controllers = []
        if controllers:
            for i in controllers:
                self._view.ui.replaceControllerControllersComboBox.addItem(
                    i["siteEntity"]["name"], userData=i["id"]
                )
            # Try to set the combo box selection to the previously selected item
            index = self._view.ui.replaceControllerControllersComboBox.findData(
                current_controller
            )
            if index >= 0:
                self._view.ui.replaceControllerControllersComboBox.setCurrentIndex(
                    index
                )
        else:
            self._view.ui.replaceControllerControllersComboBox.addItem(
                "No controllers found"
            )

    def handle_close(self, event: QCloseEvent):
        """Save the config on close."""
        self._wifi_model.save_to_config()
        self._config.save_config()
        event.accept()
