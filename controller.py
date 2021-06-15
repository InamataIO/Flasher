import platform

from PySide2.QtCore import QThreadPool, QUrl
from PySide2.QtGui import QCloseEvent, QDesktopServices

from config import Config
from flash_model import FlashModel
from main_view import MainView
from server_model import ServerModel
from wifi_model import WiFiModel
from worker import Worker, WorkerError, WorkerInformation, WorkerWarning


class Controller:
    #####################
    # Setup functionality

    def __init__(
        self,
        server_model: ServerModel,
        flash_model: FlashModel,
        wifi_model: WiFiModel,
        view: MainView,
        config: Config,
    ):
        self._server_model = server_model
        self._flash_model = flash_model
        self._wifi_model = wifi_model
        self._view = view
        self._config = config

        self.threadpool = QThreadPool()
        self._connect_signals()
        self._connect_model_views()
        self._page_after_add_wifi = None
        self._page_before_add_wifi = None
        if server_model.is_authenticated():
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
        self._view.ui.signUpButton.clicked.connect(self.sign_up)
        self._view.ui.emailLineEdit.setText(self._server_model.get_username())
        self._view.ui.emailLineEdit.returnPressed.connect(
            self._view.ui.loginButton.click
        )
        self._view.ui.passwordLineEdit.returnPressed.connect(
            self._view.ui.loginButton.click
        )

        # Welcome Page
        self._view.ui.welcomeAddControllerButton.clicked.connect(self.to_add_controller)
        self._view.ui.welcomeReplaceControllerButton.clicked.connect(
            self.to_replace_controller
        )
        self._view.ui.welcomeManageWiFiButton.clicked.connect(self.to_manage_wifi)
        self._view.ui.welcomeLogOutPushButton.clicked.connect(self.log_out)
        self._view.ui.welcomeUsername.setText(self._server_model.get_username())

        # Add Controller Page
        self._view.ui.addControllerFlashButton.clicked.connect(
            self.add_controller_download_and_flash
        )
        self._view.ui.addControllerReloadButton.clicked.connect(
            self.add_controller_reload
        )
        self._view.ui.addControllerBackButton.clicked.connect(self.to_welcome_page)
        self._view.ui.addControllerDriverButton.clicked.connect(self.to_driver_install)

        # Replace Controller Page
        self._view.ui.replaceControllerSitesComboBox.currentIndexChanged.connect(
            self.replace_controller_site_selected
        )
        self._view.ui.replaceControllerFlashButton.clicked.connect(
            self.replace_controller_download_and_flash
        )
        self._view.ui.replaceControllerReloadButton.clicked.connect(
            self.replace_controller_reload
        )
        self._view.ui.replaceControllerBackButton.clicked.connect(self.to_welcome_page)
        self._view.ui.replaceControllerDriverButton.clicked.connect(
            self.to_driver_install
        )

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

    def to_driver_install(self):
        """Open the driver installation web page."""
        QDesktopServices.openUrl(
            QUrl("https://github.com/protohaus/sdg-flasher#driver-setup-instructions")
        )

    ##########################
    # Login Page Functionality

    def log_in(self):
        """Log the user in and save the auth token."""
        self._view.ui.loginLoadingText.show()
        self._view.ui.loginLoadingBar.show()
        email = self._view.ui.emailLineEdit.text()
        password = self._view.ui.passwordLineEdit.text()
        worker = Worker(self._server_model.log_in, email, password)
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

    def log_in_error(self, error):
        """Error handler for the login thread."""
        self.handle_error(error)

    def sign_up(self):
        QDesktopServices.openUrl(QUrl("https://core.openfarming.ai/"))

    ############################
    # Welcome Page Functionality

    def log_out(self):
        """Log the user out and clear the password and auth token."""
        self._server_model.log_out()
        self._view.ui.passwordLineEdit.clear()
        self._view.change_page(self._view.Pages.LOGIN)

    def to_add_controller(self):
        """Request to switch to the add controller page. Go to add wifi if none exist."""
        if self._wifi_model.ap_count():
            self._view.change_page(self._view.Pages.ADD_CONTROLLER)
        else:
            self._page_after_add_wifi = self._view.Pages.ADD_CONTROLLER
            self._page_before_add_wifi = self._view.Pages.WELCOME
            self._view.change_page(self._view.Pages.ADD_WIFI)

    def to_replace_controller(self):
        """Request to switch to the replace controller page. Go to add wifi if none exist."""
        if self._wifi_model.ap_count():
            self._view.change_page(self._view.Pages.REPLACE_CONTROLLER)
        else:
            self._page_after_add_wifi = self._view.Pages.REPLACE_CONTROLLER
            self._page_before_add_wifi = self._view.Pages.WELCOME
            self._view.change_page(self._view.Pages.ADD_WIFI)

    def to_manage_wifi(self):
        """Request to switch to the mange page. Go to add wifi if none exist."""
        if self._wifi_model.ap_count():
            self._view.change_page(self._view.Pages.MANAGE_WIFI)
        else:
            self._page_after_add_wifi = self._view.Pages.MANAGE_WIFI
            self._page_before_add_wifi = self._view.Pages.WELCOME
            self._view.change_page(self._view.Pages.ADD_WIFI)

    #############################
    # Add WiFi Page Functionality

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
        else:
            self._view.change_page(self._view.Pages.WELCOME)

    ################################
    # Manage WiFi Page Functionality

    def manage_wifi_to_add_wifi(self):
        self._page_before_add_wifi = self._view.Pages.MANAGE_WIFI
        self._page_after_add_wifi = self._view.Pages.MANAGE_WIFI
        self._view.change_page(self._view.Pages.ADD_WIFI)

    def remove_wifi_ap(self):
        """Remove the currently selected WiFi AP."""
        if indexes := self._view.ui.apListView.selectedIndexes():
            self._wifi_model.remove_ap(indexes[0].row())

    ##############################
    # Add controller functionality

    def handle_add_controller_page(self):
        """Get data and populate the combo boxes on the add controller page."""
        if self._config.config.get("sites"):
            self.handle_add_controller_page_result(None)
        else:
            self._view.ui.addControllerLoadingText.show()
            self._view.ui.addControllerLoadingBar.show()
            worker = Worker(self._server_model.get_site_and_firmware_data)
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
        if not self._view.ui.addControllerSitesComboBox.count():
            self._view.notify(
                "No sites found. Visit <a href='https://core.openfarming.ai' style='color: #ccc'>core.openfarming.ai</a> to create new sites.",
                "No Sites Found",
            )

        # Update the firmware combo box and retain the currently selected item
        current_firmware = self._view.ui.addControllerFirmwaresComboBox.currentData()
        self._view.ui.addControllerFirmwaresComboBox.clear()
        for i in self._config.config.get("firmwareImages", []):
            self._view.ui.addControllerFirmwaresComboBox.addItem(
                f"{i['name']} {i['version']}", userData=i["id"]
            )
        if current_firmware:
            index = self._view.ui.addControllerFirmwaresComboBox.findData(
                current_firmware
            )
            if index:
                self._view.ui.addControllerFirmwaresComboBox.setCurrentIndex(index)

    def handle_add_controller_page_error(self, error):
        """Error handler for the add controller data fetch thread."""
        self.handle_error(error)

    def handle_add_controller_page_finished(self):
        """Hide the loading widgets for the add controller page."""
        self._view.ui.addControllerLoadingText.hide()
        self._view.ui.addControllerLoadingBar.hide()

    def add_controller_reload(self):
        """Clear the cached data and repopulate the combo boxes."""
        self._config.clear_cached_data()
        self.handle_add_controller_page()

    def add_controller_download_and_flash(self):
        """Download the selected firmware image and flash it to the ESP."""
        if not self.add_controller_is_flash_input_valid():
            return
        self._view.ui.addControllerProgressText.setText("Get Firmware (1/4)")
        self.add_controller_set_widgets_for_flashing(True)

        firmware_id = self._view.ui.addControllerFirmwaresComboBox.currentData()
        worker = Worker(self._server_model.download_firmware_image, firmware_id)
        worker.signals.progress.connect(self.add_controller_download_firmware_progress)
        worker.signals.result.connect(self.add_controller_download_firmware_result)
        worker.signals.error.connect(self.add_controller_download_firmware_error)
        self.threadpool.start(worker)

    def add_controller_is_flash_input_valid(self):
        """Checks the user input and returns true if it looks good."""
        if not self._view.ui.addControllerSitesComboBox.currentData():
            message = (
                "Please select a site or reload if none are available."
                " If the problem persists please update the OFAI Flasher tool or contact your administrator."
            )
            self._view.notify(message, "Missing Input")
            return False
        if not self._view.ui.addControllerNameLineEdit.text():
            message = "Please enter a name for the new controller."
            self._view.notify(message, "Missing Input")
            return False
        if not self._view.ui.addControllerAPListView.selectedIndexes():
            message = (
                "Please select one or more WiFi access points to be used by the controller."
                " To add or change entries, go to the 'Manager WiFi' page."
            )
            self._view.notify(message, "Missing Input")
            return False
        if not self._view.ui.addControllerFirmwaresComboBox.currentData():
            message = (
                "Please select a firmware version or reload if none are available."
                " If the problem persists please update the OFAI Flasher tool or contact your administrator."
            )
            self._view.notify(message, "Missing Input")
            return False
        return True

    def add_controller_download_firmware_progress(self, progress):
        """Set the download progress."""
        self.add_controller_set_progress_bar(progress)

    def add_controller_download_firmware_result(self, firmware: dict):
        """After completing the download, flash the controller."""
        self._view.ui.addControllerProgressText.setText("Get Bootloader (2/4)")
        self.add_controller_set_progress_bar(0)

        bootloader_id = firmware["bootloader"]["id"]
        worker = Worker(self._server_model.download_bootloader_image, bootloader_id)
        worker.signals.progress.connect(
            self.add_controller_download_bootloader_progress
        )
        worker.signals.result.connect(self.add_controller_download_bootloader_result)
        worker.signals.error.connect(self.add_controller_download_bootloader_error)
        self.threadpool.start(worker)

    def add_controller_download_firmware_error(self, error):
        """Handle errors while downloading the firmware."""
        self.add_controller_set_widgets_for_flashing(False)
        self.handle_error(error)

    def add_controller_download_bootloader_progress(self, progress):
        """Set the download progress."""
        self.add_controller_set_progress_bar(progress)

    def add_controller_download_bootloader_result(self, bootloader: dict):
        """After completing the bootloader download, register the controller."""
        self._view.ui.addControllerProgressText.setText("Registering (3/4)")
        self.add_controller_set_progress_bar(0)

        name = self._view.ui.addControllerNameLineEdit.text()
        site_id = self._view.ui.addControllerSitesComboBox.currentData()
        controller_type_id = self._config.config["controllerComponentTypes"][0]["id"]
        firmware_id = self._view.ui.addControllerFirmwaresComboBox.currentData()

        worker = Worker(
            self._server_model.register_controller,
            name,
            site_id,
            controller_type_id,
            firmware_id,
        )
        worker.signals.result.connect(self.add_controller_register_result)
        worker.signals.error.connect(self.add_controller_register_error)
        self.threadpool.start(worker)

    def add_controller_download_bootloader_error(self, error):
        """Handle errors while downloading the bootloader."""
        self.add_controller_set_widgets_for_flashing(False)
        self.handle_error(error)

    def add_controller_register_result(self, controller):
        """After registering a new controller, start the flashing process."""
        self._view.ui.addControllerProgressText.setText("Flashing (4/4)")
        self.add_controller_set_progress_bar(0)

        # Get the WiFi APs selected in the QListView
        indexes = self._view.ui.addControllerAPListView.selectedIndexes()
        wifi_aps = [self._wifi_model.get_ap(i) for i in indexes]

        if platform.system() == "Windows":
            self._view.notify(
                "Please press and hold the boot button on the ESP32 until the flash process starts.",
                "Enable Flash Mode",
            )

        # Start a task to flash the controller
        worker = Worker(self._flash_model.flash_controller, controller, wifi_aps)
        worker.signals.progress.connect(self.add_controller_flash_progress)
        worker.signals.result.connect(self.add_controller_flash_result)
        worker.signals.error.connect(self.add_controller_flash_error)
        worker.signals.finished.connect(self.add_controller_flash_finished)
        self.threadpool.start(worker)

    def add_controller_register_error(self, error):
        """Handle errors when registering a new controller."""
        self.add_controller_set_widgets_for_flashing(False)
        self.handle_error(error)

    def add_controller_flash_progress(self, progress):
        self.add_controller_set_progress_bar(progress)

    def add_controller_flash_result(self, _):
        message = "Successfully flashed the microcontroller."
        self._view.notify(message, "Finished Flashing", "information")

    def add_controller_flash_error(self, error):
        """Handle errors while flashing the controller."""
        self.handle_error(error)

    def add_controller_flash_finished(self):
        """Handle the end (success or error) of flashing the controller."""
        self.add_controller_set_widgets_for_flashing(False)

    def add_controller_set_widgets_for_flashing(self, is_flashing: bool):
        """Disable or enable all add controller widgets."""
        if is_flashing:
            self._view.ui.addControllerProgressText.show()
            self.add_controller_set_progress_bar(0)
            self._view.ui.addControllerProgressBar.show()
        else:
            self._view.ui.addControllerProgressText.hide()
            self._view.ui.addControllerProgressBar.hide()

        self._view.ui.addControllerSitesComboBox.setDisabled(is_flashing)
        self._view.ui.addControllerNameLineEdit.setDisabled(is_flashing)
        self._view.ui.addControllerAPListView.setDisabled(is_flashing)
        self._view.ui.addControllerFirmwaresComboBox.setDisabled(is_flashing)
        self._view.ui.addControllerFlashButton.setDisabled(is_flashing)
        self._view.ui.addControllerReloadButton.setDisabled(is_flashing)
        self._view.ui.addControllerBackButton.setDisabled(is_flashing)

    def add_controller_set_progress_bar(self, progress: int) -> None:
        """Set the progress bar for the add controller page."""
        if progress < 0:
            self._view.ui.addControllerProgressBar.setValue(-1)
            self._view.ui.addControllerProgressBar.setRange(0, 0)
        else:
            limited_progress = min(progress, 100)
            self._view.ui.addControllerProgressBar.setValue(limited_progress)
            self._view.ui.addControllerProgressBar.setRange(0, 100)

    ##############################
    # Replace controller functionality

    def handle_replace_controller_page(self):
        """Fetch data and populate the combo boxes for the replace controller page."""
        if self._config.config.get("sites"):
            self.handle_replace_controller_page_result(None)
        else:
            self._view.ui.replaceControllerLoadingText.show()
            self._view.ui.replaceControllerLoadingBar.show()
            worker = Worker(self._server_model.get_site_and_firmware_data)
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
        if not self._view.ui.replaceControllerSitesComboBox.count():
            self._view.notify(
                "No sites found. Visit <a href='https://core.openfarming.ai' style='color: #ccc'>core.openfarming.ai</a> to create new sites.",
                "No Sites Found",
            )
        
        # Update the firmware combo box and retain the currently selected item
        current_firmware = (
            self._view.ui.replaceControllerFirmwaresComboBox.currentData()
        )
        self._view.ui.replaceControllerFirmwaresComboBox.clear()
        for i in self._config.config.get("firmwareImages", []):
            self._view.ui.replaceControllerFirmwaresComboBox.addItem(
                f"{i['name']} {i['version']}", userData=i["id"]
            )
        if current_firmware:
            index = self._view.ui.replaceControllerFirmwaresComboBox.findData(
                current_firmware
            )
            if index >= 0:
                self._view.ui.replaceControllerFirmwaresComboBox.setCurrentIndex(index)

    def handle_replace_controller_page_error(self, error):
        """Error handler for the replace controller data fetch thread."""
        self.handle_error(error)

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
        worker = Worker(self._server_model.get_controller_data, site_id)
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

    def replace_controller_load_controllers_error(self, error):
        """Error handler for fetching the controllers thread."""
        self.handle_error(error)

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

    def replace_controller_download_and_flash(self):
        """Download the selected firmware image and flash it to the ESP."""
        if not self.replace_controller_is_flash_input_valid():
            return
        self._view.ui.replaceControllerProgressText.setText("Get Firmware (1/4)")
        self.replace_controller_set_widgets_for_flashing(True)

        firmware_id = self._view.ui.replaceControllerFirmwaresComboBox.currentData()
        worker = Worker(self._server_model.download_firmware_image, firmware_id)
        worker.signals.progress.connect(
            self.replace_controller_download_firmware_progress
        )
        worker.signals.result.connect(self.replace_controller_download_firmware_result)
        worker.signals.error.connect(self.replace_controller_download_firmware_error)
        self.threadpool.start(worker)

    def replace_controller_is_flash_input_valid(self) -> bool:
        """Checks the user input and returns true is it looks good."""
        if not self._view.ui.replaceControllerSitesComboBox.currentData():
            message = (
                "Please select a site or reload if none are available."
                " If the problem persists please update the OFAI Flasher tool or contact your administrator."
            )
            self._view.notify(message, "Missing Input")
            return False
        if not self._view.ui.replaceControllerControllersComboBox.currentData():
            message = (
                "Please select a site or reload if none are available."
                " If the problem persists please update the OFAI Flasher tool or contact your administrator."
            )
            self._view.notify(message, "Missing Input")
            return False
        if not self._view.ui.replaceControllerAPListView.selectedIndexes():
            message = (
                "Please select one or more WiFi access points to be used by the controller."
                " To add or change entries, go to the 'Manager WiFi' page."
            )
            self._view.notify(message, "Missing Input")
            return False
        if not self._view.ui.replaceControllerFirmwaresComboBox.currentData():
            message = (
                "Please select a firmware version or reload if none are available."
                " If the problem persists please update the OFAI Flasher tool or contact your administrator."
            )
            self._view.notify(message, "Missing Input")
            return False
        return True

    def replace_controller_set_widgets_for_flashing(self, is_flashing: bool):
        """Disable or enable all add controller widgets."""
        if is_flashing:
            self._view.ui.replaceControllerProgressText.show()
            self._view.ui.replaceControllerProgressBar.setValue(0)
            self._view.ui.replaceControllerProgressBar.setRange(0, 100)
            self._view.ui.replaceControllerProgressBar.show()
        else:
            self._view.ui.replaceControllerProgressText.hide()
            self._view.ui.replaceControllerProgressBar.hide()

        self._view.ui.replaceControllerSitesComboBox.setDisabled(is_flashing)
        self._view.ui.replaceControllerControllersComboBox.setDisabled(is_flashing)
        self._view.ui.replaceControllerAPListView.setDisabled(is_flashing)
        self._view.ui.replaceControllerFirmwaresComboBox.setDisabled(is_flashing)
        self._view.ui.replaceControllerFlashButton.setDisabled(is_flashing)
        self._view.ui.replaceControllerReloadButton.setDisabled(is_flashing)
        self._view.ui.replaceControllerBackButton.setDisabled(is_flashing)

    def replace_controller_download_firmware_progress(self, progress):
        """Set the download progress as half of the download and flash progress."""
        self.replace_controller_set_progress_bar(progress)

    def replace_controller_download_firmware_result(self, firmware: dict):
        """After completing the download, flash the controller."""
        self._view.ui.replaceControllerProgressText.setText("Get Bootloader (2/4)")
        self.replace_controller_set_progress_bar(0)

        bootloader_id = firmware["bootloader"]["id"]
        worker = Worker(self._server_model.download_bootloader_image, bootloader_id)
        worker.signals.progress.connect(
            self.replace_controller_download_bootloader_progress
        )
        worker.signals.result.connect(
            self.replace_controller_download_bootloader_result
        )
        worker.signals.error.connect(self.replace_controller_download_bootloader_error)
        self.threadpool.start(worker)

    def replace_controller_download_firmware_error(self, error):
        """Handle errors while downloading the firmware."""
        self.replace_controller_set_widgets_for_flashing(False)
        self.handle_error(error)

    def replace_controller_download_bootloader_progress(self, progress):
        """Set the download progress."""
        self.replace_controller_set_progress_bar(progress)

    def replace_controller_download_bootloader_result(self, bootloader_image: dict):
        """After completing the download, flash the controller."""
        self._view.ui.replaceControllerProgressText.setText("Registering (3/4)")
        self._view.ui.replaceControllerProgressBar.setValue(0)

        controller_id = self._view.ui.replaceControllerControllersComboBox.currentData()
        site_id = self._view.ui.replaceControllerSitesComboBox.currentData()
        firmware_id = self._view.ui.replaceControllerFirmwaresComboBox.currentData()

        worker = Worker(
            self._server_model.update_controller, controller_id, site_id, firmware_id
        )
        worker.signals.result.connect(self.replace_controller_update_result)
        worker.signals.error.connect(self.replace_controller_update_error)
        self.threadpool.start(worker)

    def replace_controller_download_bootloader_error(self, error):
        """Handle errors when downloading the firmware."""
        self.replace_controller_set_widgets_for_flashing(False)
        self.handle_error(error)

    def replace_controller_update_result(self, controller):
        """After updating the controller, cycle its auth token."""
        self._view.ui.replaceControllerProgressBar.setValue(50)

        controller_id = controller["id"]
        site_id = self._view.ui.replaceControllerSitesComboBox.currentData()

        worker = Worker(
            self._server_model.cycle_controller_auth_token, controller_id, site_id
        )
        worker.signals.result.connect(self.replace_controller_cycle_token_result)
        worker.signals.error.connect(self.replace_controller_cycle_token_error)
        self.threadpool.start(worker)

    def replace_controller_update_error(self, error):
        """Handle errors when updating the controller."""
        self.replace_controller_set_widgets_for_flashing(False)
        self.handle_error(error)

    def replace_controller_cycle_token_result(self, controller):
        """After updating the controller's auth key, flash it."""
        self._view.ui.replaceControllerProgressText.setText("Flashing (4/4)")
        self._view.ui.replaceControllerProgressBar.setValue(0)

        # Get the WiFi APs selected in the QListView
        indexes = self._view.ui.replaceControllerAPListView.selectedIndexes()
        wifi_aps = [self._wifi_model.get_ap(i) for i in indexes]

        # Notify the user to hold the flash (boot) button
        if platform.system() == "Windows":
            self._view.notify(
                "Please press and hold the boot button on the ESP32 until the flash process starts.",
                "Enable Flash Mode",
            )

        # Start a task to flash the controller
        worker = Worker(self._flash_model.flash_controller, controller, wifi_aps)
        worker.signals.progress.connect(self.replace_controller_flash_progress)
        worker.signals.result.connect(self.replace_controller_flash_result)
        worker.signals.error.connect(self.replace_controller_flash_error)
        worker.signals.finished.connect(self.replace_controller_flash_finished)
        self.threadpool.start(worker)

    def replace_controller_cycle_token_error(self, error):
        """Handle errors when cycling a controller's auth token."""
        self.replace_controller_set_widgets_for_flashing(False)
        self.handle_error(error)

    def replace_controller_flash_progress(self, progress: int) -> None:
        """Handle the update when flashing the controller."""
        self.replace_controller_set_progress_bar(progress)

    def replace_controller_flash_result(self, _) -> None:
        message = "Successfully flashed the microcontroller."
        self._view.notify(message, "Finished Flashing", "information")

    def replace_controller_flash_error(self, error: WorkerError) -> None:
        """Handle an error when flashing."""
        self.replace_controller_set_widgets_for_flashing(False)
        self.handle_error(error)

    def replace_controller_flash_finished(self) -> None:
        """Handle the end (success or error) of flashing the controller."""
        self.replace_controller_set_widgets_for_flashing(False)

    def replace_controller_set_progress_bar(self, progress: int) -> None:
        """Update the progress bar of the replace controller page."""
        if progress < 0:
            self._view.ui.replaceControllerProgressBar.setValue(-1)
            self._view.ui.replaceControllerProgressBar.setRange(0, 0)
        else:
            limited_progress = min(progress, 100)
            self._view.ui.replaceControllerProgressBar.setValue(limited_progress)
            self._view.ui.replaceControllerProgressBar.setRange(0, 100)

    ##############################
    # Miscellaneous functionality

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

    def handle_close(self, event: QCloseEvent):
        """Save the config on close."""
        self._wifi_model.save_to_config()
        self._config.save_config()
        event.accept()
