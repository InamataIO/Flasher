import platform
from typing import List

from PySide6.QtCore import QCoreApplication, QThreadPool, QUrl, Slot
from PySide6.QtGui import QCloseEvent, QDesktopServices, QKeySequence, QShortcut
from PySide6.QtWidgets import QMenu

from config import Config, ControllerModel
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
        app: QCoreApplication,
    ):
        self._server_model = server_model
        self._flash_model = flash_model
        self._wifi_model = wifi_model
        self._view = view
        self._config = config
        self._app = app

        self.threadpool = QThreadPool()
        self._connect_signals()
        self._connect_model_views()
        self._connect_shortcuts()
        self._page_after_add_wifi = None
        self._page_before_add_wifi = None
        view.change_page(view.Pages.LOGIN)
        # Call login page handler if change_page does not result in a page change
        self.handle_login_page()
        self.auto_log_in()

    def _connect_signals(self):
        """Connect widget signals to the appropriate function."""
        # Main Application
        self._view.close_callback = self.handle_close
        self._view.ui.stackedWidget.currentChanged.connect(self.page_changed)

        # Login Page
        self._view.ui.loginButton.clicked.connect(self.log_in)
        self._view.ui.signUpButton.clicked.connect(self.sign_up)
        #   Login system menu
        self.loginSystemMenu = QMenu()
        self.loginSystemMenu.addAction("Clear data", self.clear_data)
        self.loginSystemMenu.addAction("Open system settings", self.to_system_settings)
        self._view.ui.loginSystemIconButton.setMenu(self.loginSystemMenu)
        self._view.ui.loginHelpIconButton.clicked.connect(self.show_help_dialog)

        # Welcome Page
        self._view.ui.welcomeAddControllerButton.clicked.connect(self.to_add_controller)
        self._view.ui.welcomeReplaceControllerButton.clicked.connect(
            self.to_replace_controller
        )
        self._view.ui.welcomeManageWiFiButton.clicked.connect(self.to_manage_wifi)
        self._view.ui.welcomeLogOutPushButton.clicked.connect(self.log_out)
        self._view.ui.welcomeHelpIconButton.clicked.connect(self.show_help_dialog)
        self.set_welcome_username(self._config.users_name)

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

        # System Settings Page
        self._view.ui.systemSettingsCancelButton.clicked.connect(
            self.back_from_system_settings
        )
        self._view.ui.systemSettingsSaveButton.clicked.connect(
            self.system_settings_save
        )
        self._view.ui.systemSettingsRestoreDefaultsButton.clicked.connect(
            self.system_settings_restore_defaults
        )
        self._view.ui.systemSettingsServerComboBox.currentIndexChanged.connect(
            self.system_settings_server_selected
        )
        self._view.ui.systemSettingsCoreServerLineEdit.editingFinished.connect(
            self.system_settings_core_server_edited
        )
        self._view.ui.systemSettingsAuthServerLineEdit.editingFinished.connect(
            self.system_settings_auth_server_edited
        )

    def _connect_model_views(self):
        """Connect models to the appropriate views."""
        self._view.ui.apListView.setModel(self._wifi_model)
        self._view.ui.addControllerAPListView.setModel(self._wifi_model)
        self._view.ui.replaceControllerAPListView.setModel(self._wifi_model)

    def _connect_shortcuts(self):
        """Connect shortcuts."""
        self.quit_shortcut = QShortcut(QKeySequence("Ctrl+Q"), self._view.ui)
        self.quit_shortcut.activated.connect(self._app.quit)

    def to_driver_install(self):
        """Open the driver installation web page."""
        QDesktopServices.openUrl(
            QUrl("https://github.com/InamataCo/Flasher#driver-setup-instructions")
        )

    ##########################
    # Login Page Functionality

    def handle_login_page(self):
        """Set the selected server text."""
        server_name = self._server_model.server_name
        if server_name == self._server_model.dev_server_name:
            server_urls = self._server_model.server_urls
            server_name = f"{server_name}\n{server_urls.core_base_url} / {server_urls.oauth_base_url}"
        self._view.ui.loginSelectedServerText.setText(server_name)

    def log_in(self):
        """Log the user in and save the auth token."""
        self._view.ui.loginLoadingText.show()
        self._view.ui.loginLoadingBar.show()
        self._view.ui.loginSelectedServerText.hide()
        worker = Worker(self._server_model.log_in)
        worker.signals.result.connect(self.log_in_result)
        worker.signals.error.connect(self.log_in_error)
        worker.signals.finished.connect(self.log_in_finished)
        self.threadpool.start(worker)

    def log_in_result(self, _):
        """If login succeeds, go to the welcome page."""
        name = self._config.config.get("name")
        if not name:
            name = self._config.config.get("username")
        self.set_welcome_username(name)
        self._view.change_page(self._view.Pages.WELCOME)

    def log_in_finished(self):
        """After the login attempt, hide the loading widgets."""
        self._view.ui.loginLoadingText.hide()
        self._view.ui.loginLoadingBar.hide()
        self._view.ui.loginSelectedServerText.show()

    def log_in_error(self, error):
        """Error handler for the login thread."""
        self.handle_error(error)

    def sign_up(self):
        QDesktopServices.openUrl(QUrl("https://app.inamata.co/"))

    def clear_data(self):
        self._server_model.restore_dev_server_urls()
        self._server_model.server_urls = self._server_model.default_server
        self._server_model.log_out()
        self._wifi_model.remove_all_aps()
        self._config.clear_stored_data()
        self.handle_login_page()
        self._view.notify(
            "Cleared secrets, configurations and cached data.", "Cleared data"
        )

    def auto_log_in(self):
        self._view.ui.loginLoadingText.show()
        self._view.ui.loginLoadingBar.show()
        self._view.ui.loginSelectedServerText.hide()
        worker = Worker(self._server_model.try_access_token_refresh)
        worker.signals.result.connect(self.auto_log_in_result)
        worker.signals.error.connect(self.auto_log_in_error)
        worker.signals.finished.connect(self.auto_log_in_finished)
        self.threadpool.start(worker)

    def auto_log_in_result(self, success: bool):
        """If the auto login succeeds, go to the welcome page."""
        if not success:
            return
        name = self._config.config.get("name")
        if not name:
            name = self._config.config.get("username")
        self.set_welcome_username(name)
        self._view.change_page(self._view.Pages.WELCOME)

    def auto_log_in_finished(self):
        """After the auto login attempt, hide the loading widgets."""
        self._view.ui.loginLoadingText.hide()
        self._view.ui.loginLoadingBar.hide()
        self._view.ui.loginSelectedServerText.show()

    def auto_log_in_error(self, error):
        """Error handler for the auto login thread."""
        self.handle_error(error)

    def to_system_settings(self):
        """Open select server dialog."""
        self._page_before_system_settings = self._view.current_page()
        self._view.change_page(self._view.Pages.SYSTEM_SETTINGS)

    ############################
    # Welcome Page Functionality

    def log_out(self):
        """Log the user out and clear the password and auth token."""
        self._server_model.log_out()
        self._config.clear_cached_data()
        self._config.save_config()
        self._view.change_page(self._view.Pages.LOGIN)

    def to_add_controller(self):
        """Request to go to add controller page. Go to add wifi if none exist."""
        if self._wifi_model.ap_count():
            self._view.change_page(self._view.Pages.ADD_CONTROLLER)
        else:
            self._page_after_add_wifi = self._view.Pages.ADD_CONTROLLER
            self._page_before_add_wifi = self._view.Pages.WELCOME
            self._view.change_page(self._view.Pages.ADD_WIFI)

    def to_replace_controller(self):
        """Request to go to replace controller page. Go to add wifi if none exist."""
        if self._wifi_model.ap_count():
            self._view.change_page(self._view.Pages.REPLACE_CONTROLLER)
        else:
            self._page_after_add_wifi = self._view.Pages.REPLACE_CONTROLLER
            self._page_before_add_wifi = self._view.Pages.WELCOME
            self._view.change_page(self._view.Pages.ADD_WIFI)

    def to_manage_wifi(self):
        """Request to go to the mange page. Go to add wifi if none exist."""
        if self._wifi_model.ap_count():
            self._view.change_page(self._view.Pages.MANAGE_WIFI)
        else:
            self._page_after_add_wifi = self._view.Pages.MANAGE_WIFI
            self._page_before_add_wifi = self._view.Pages.WELCOME
            self._view.change_page(self._view.Pages.ADD_WIFI)

    def set_welcome_username(self, username: str) -> None:
        text = f"{self._server_model.server_name.capitalize()}: {username}"
        self._view.ui.welcomeUsername.setText(text)

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
        if self._config.has_cached_sites():
            self.handle_add_controller_page_result(None)
        else:
            self._view.ui.addControllerSerialPortsText.hide()
            self._view.ui.addControllerLoadingText.show()
            self._view.ui.addControllerLoadingBar.show()
            worker = Worker(self._server_model.get_site_and_firmware_data)
            worker.signals.result.connect(self.handle_add_controller_page_result)
            worker.signals.error.connect(self.handle_add_controller_page_error)
            worker.signals.finished.connect(self.handle_add_controller_page_finished)
            self.threadpool.start(worker)

    def handle_add_controller_page_result(self, _):
        """Populate the combo boxes with the fetched data for add controller page."""
        # Update the site combo box and retain the currently selected item
        current_site = self._view.ui.addControllerSitesComboBox.currentData()
        self._view.ui.addControllerSitesComboBox.clear()
        for i in self._config.get_sites():
            self._view.ui.addControllerSitesComboBox.addItem(i.name, userData=i.id)
        if current_site:
            index = self._view.ui.addControllerSitesComboBox.findData(current_site)
            if index:
                self._view.ui.addControllerSitesComboBox.setCurrentIndex(index)
        if not self._view.ui.addControllerSitesComboBox.count():
            self._view.notify(
                "No sites found. Visit <a href='https://app.inamata.co'"
                " style='color: #ccc'>app.inamata.co</a> to create new sites.",
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

        # Update the found serial ports
        text = self.get_found_serial_ports_text()
        self._view.ui.addControllerSerialPortsText.setText(text)

    def handle_add_controller_page_error(self, error):
        """Error handler for the add controller data fetch thread."""
        self.handle_error(error)

    def handle_add_controller_page_finished(self):
        """Hide the loading widgets for the add controller page."""
        self._view.ui.addControllerLoadingText.hide()
        self._view.ui.addControllerLoadingBar.hide()
        self._view.ui.addControllerSerialPortsText.show()

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
                " If the problem persists please update the Inamata Flasher tool or"
                " contact your administrator."
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
                " If the problem persists please update the Inamata Flasher tool or contact your administrator."
            )
            self._view.notify(message, "Missing Input")
            return False
        return True

    def add_controller_download_firmware_progress(self, progress):
        """Set the download progress for 0% to 30%."""
        mapped_progress = progress / 100 * 30
        self.add_controller_set_progress_bar(mapped_progress)

    def add_controller_download_firmware_result(self, firmware: dict):
        """After completing the download, flash the controller."""
        self._view.ui.addControllerProgressText.setText("Get Bootloader (2/4)")
        self.add_controller_set_progress_bar(30)

        bootloader = firmware["bootloader"]
        if not bootloader:
            return self.add_controller_download_bootloader_result({})
        worker = Worker(self._server_model.download_bootloader_image, bootloader["id"])
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
        """Set the download progress from 30% to 40%."""
        mapped_progress = (progress / 100 * 10) + 30
        self.add_controller_set_progress_bar(mapped_progress)

    def add_controller_download_bootloader_result(self, bootloader: dict):
        """After completing the bootloader download, register the controller."""
        self._view.ui.addControllerProgressText.setText("Registering (3/4)")
        self.add_controller_set_progress_bar(40)

        name = self._view.ui.addControllerNameLineEdit.text()
        site_id = self._view.ui.addControllerSitesComboBox.currentData()
        controller_type_id = self._config.config["controllerTypes"][0]["id"]
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
        self.add_controller_set_progress_bar(50)

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
        worker.signals.error.connect(
            lambda error: self.add_controller_flash_error(error, controller)
        )
        worker.signals.finished.connect(self.add_controller_flash_finished)
        self.threadpool.start(worker)

    def add_controller_register_error(self, error):
        """Handle errors when registering a new controller."""
        self.add_controller_set_widgets_for_flashing(False)
        self.handle_error(error)

    def add_controller_flash_progress(self, progress):
        """Set the flash progress from 50% to 100%."""
        mapped_progress = (progress / 100 * 50) + 50
        self.add_controller_set_progress_bar(mapped_progress)

    def add_controller_flash_result(self, _):
        message = "Successfully flashed the microcontroller."
        self._view.notify(message, "Finished Flashing", "information")

    def add_controller_flash_error(self, error, controller):
        """Handle errors while flashing the controller."""
        try:
            self._server_model.delete_controller(controller.id)
        except WorkerError as err:
            self.handle_error(err)
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

    #######################################
    # Replace Controller Page Functionality

    def handle_replace_controller_page(self):
        """Fetch data and populate the combo boxes for the replace controller page."""
        if self._config.has_cached_sites():
            self.handle_replace_controller_page_result(None)
        else:
            self._view.ui.replaceControllerSerialPortsText.hide()
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
        for i in self._config.get_sites():
            self._view.ui.replaceControllerSitesComboBox.addItem(i.name, userData=i.id)
        self._view.ui.replaceControllerSitesComboBox.blockSignals(False)
        index = self._view.ui.replaceControllerSitesComboBox.findData(current_site)
        if index >= 0:
            self._view.ui.replaceControllerSitesComboBox.setCurrentIndex(index)
        else:
            self._view.ui.replaceControllerSitesComboBox.currentIndexChanged.emit(0)
        if not self._view.ui.replaceControllerSitesComboBox.count():
            self._view.notify(
                "No sites found. Visit <a href='https://app.inamata.co' style='color: #ccc'>app.inamata.co</a> to create new sites.",
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

        text = self.get_found_serial_ports_text()
        self._view.ui.replaceControllerSerialPortsText.setText(text)

    def handle_replace_controller_page_error(self, error):
        """Error handler for the replace controller data fetch thread."""
        self.handle_error(error)

    def handle_replace_controller_page_finished(self):
        """Hide the loading widgets for the replace controller page."""
        self._view.ui.replaceControllerLoadingText.hide()
        self._view.ui.replaceControllerLoadingBar.hide()
        self._view.ui.replaceControllerSerialPortsText.show()

    def replace_controller_reload(self):
        """Clear cached data and repopulate the combo boxes on the replace controller page."""
        self._config.clear_cached_data()
        self.handle_replace_controller_page()

    def replace_controller_site_selected(self, index):
        """Start the process to populate the controller combo box for the selected site."""
        if site_id := self._view.ui.replaceControllerSitesComboBox.itemData(index):
            controllers = self._config.get_controllers_by_site(site_id)
            if controllers:
                self.populate_replace_controller_controllers(controllers)
            else:
                self.replace_controller_load_controllers(site_id)

    def replace_controller_load_controllers(self, site_id):
        """Fetch available controllers for the selected site."""
        self._view.ui.replaceControllerSerialPortsText.hide()
        self._view.ui.replaceControllerLoadingText.show()
        self._view.ui.replaceControllerLoadingBar.show()
        worker = Worker(self._server_model.get_controller_data, site_id)
        worker.signals.result.connect(self.replace_controller_load_controllers_result)
        worker.signals.error.connect(self.replace_controller_load_controllers_error)
        worker.signals.finished.connect(
            self.replace_controller_load_controllers_finished
        )
        self.threadpool.start(worker)

    def replace_controller_load_controllers_result(
        self, controllers: List[ControllerModel]
    ):
        """Populate the controller combo box with the fetched data."""
        self.populate_replace_controller_controllers(controllers)

    def replace_controller_load_controllers_error(self, error):
        """Error handler for fetching the controllers thread."""
        self.handle_error(error)

    def replace_controller_load_controllers_finished(self):
        """Hide the loading widgets on the replace controller page."""
        self._view.ui.replaceControllerLoadingText.hide()
        self._view.ui.replaceControllerLoadingBar.hide()
        self._view.ui.replaceControllerSerialPortsText.show()

    def populate_replace_controller_controllers(
        self, controllers: List[ControllerModel]
    ):
        """Populate the controller combo box for the selected site."""
        # Save the current item to restore the combo box selection later
        current_controller = (
            self._view.ui.replaceControllerControllersComboBox.currentData()
        )
        self._view.ui.replaceControllerControllersComboBox.clear()
        if not controllers:
            self._view.ui.replaceControllerControllersComboBox.addItem(
                "No controllers found"
            )
            return

        controllers.sort(key=lambda c: c.name)
        for i in controllers:
            self._view.ui.replaceControllerControllersComboBox.addItem(
                i.name, userData=i.id
            )
        # Try to set the combo box selection to the previously selected item
        index = self._view.ui.replaceControllerControllersComboBox.findData(
            current_controller
        )
        if index >= 0:
            self._view.ui.replaceControllerControllersComboBox.setCurrentIndex(index)

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
                " If the problem persists please update the Inamata Flasher tool or contact your administrator."
            )
            self._view.notify(message, "Missing Input")
            return False
        if not self._view.ui.replaceControllerControllersComboBox.currentData():
            message = (
                "Please select a site or reload if none are available."
                " If the problem persists please update the Inamata Flasher tool or contact your administrator."
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
                " If the problem persists please update the Inamata Flasher tool or contact your administrator."
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
        """Set download progress for 0% to 30%."""
        mapped_progress = progress / 100 * 30
        self.replace_controller_set_progress_bar(mapped_progress)

    def replace_controller_download_firmware_result(self, firmware: dict):
        """After completing the download, flash the controller."""
        self._view.ui.replaceControllerProgressText.setText("Get Bootloader (2/4)")
        self.replace_controller_set_progress_bar(30)

        bootloader = firmware["bootloader"]
        if not bootloader:
            return self.replace_controller_download_bootloader_result({})
        worker = Worker(self._server_model.download_bootloader_image, bootloader["id"])
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
        """Set the download progress for 30% to 40%."""
        mapped_progress = (progress / 100 * 10) + 30
        self.replace_controller_set_progress_bar(mapped_progress)

    def replace_controller_download_bootloader_result(self, bootloader_image: dict):
        """After completing the download, flash the controller."""
        self._view.ui.replaceControllerProgressText.setText("Registering (3/4)")
        self._view.ui.replaceControllerProgressBar.setValue(40)

        controller_id = self._view.ui.replaceControllerControllersComboBox.currentData()
        controller = self._config.get_controller(controller_id)
        if not controller:
            self._view.notify(
                "Controller not found in cache. Please clear cached data and try again.",
                "Missing cached data",
                "critical",
            )
            return
        controller.firmware_image_id = (
            self._view.ui.replaceControllerFirmwaresComboBox.currentData()
        )
        worker = Worker(self._server_model.update_controller, controller)
        worker.signals.result.connect(self.replace_controller_update_result)
        worker.signals.error.connect(self.replace_controller_update_error)
        self.threadpool.start(worker)

    def replace_controller_download_bootloader_error(self, error):
        """Handle errors when downloading the firmware."""
        self.replace_controller_set_widgets_for_flashing(False)
        self.handle_error(error)

    def replace_controller_update_result(self, controller: ControllerModel):
        """After updating the controller, cycle its auth token."""
        self._view.ui.replaceControllerProgressBar.setValue(45)

        worker = Worker(self._server_model.cycle_controller_auth_token, controller.id)
        worker.signals.result.connect(self.replace_controller_cycle_token_result)
        worker.signals.error.connect(self.replace_controller_cycle_token_error)
        self.threadpool.start(worker)

    def replace_controller_update_error(self, error):
        """Handle errors when updating the controller."""
        self.replace_controller_set_widgets_for_flashing(False)
        self.handle_error(error)

    def replace_controller_cycle_token_result(self, controller: ControllerModel):
        """After updating the controller's auth key, flash it."""
        self._view.ui.replaceControllerProgressText.setText("Flashing (4/4)")
        self._view.ui.replaceControllerProgressBar.setValue(50)

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
        """Set the flash progress for 50% to 100%."""
        mapped_progress = (progress / 100 * 50) + 50
        self.replace_controller_set_progress_bar(mapped_progress)

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
    # System Settings Page functionality

    def handle_system_settings_page(self):
        self.system_settings_dev_server_urls = self._server_model.dev_server_urls
        if not self._view.ui.systemSettingsServerComboBox.count():
            for i in self._server_model.known_server_urls.keys():
                self._view.ui.systemSettingsServerComboBox.addItem(
                    i.capitalize(), userData=i
                )
        index = self._view.ui.systemSettingsServerComboBox.findData(
            self._server_model.server_name
        )
        self._view.ui.systemSettingsServerComboBox.setCurrentIndex(index)

    def back_from_system_settings(self):
        if self._page_before_system_settings:
            self._view.change_page(self._page_before_system_settings)
            self._page_before_system_settings = None
        else:
            self._view.change_page(self._view.Pages.LOGIN)

    def system_settings_save(self):
        """Save server settings."""
        index = self._view.ui.systemSettingsServerComboBox.currentIndex()
        server_name = self._view.ui.systemSettingsServerComboBox.itemData(index)
        if server_name == self._server_model.dev_server_name:
            new_server_urls = ServerModel.ServerUrls(
                core_base_url=self._view.ui.systemSettingsCoreServerLineEdit.text(),
                oauth_base_url=self._view.ui.systemSettingsAuthServerLineEdit.text(),
            )
            if new_server_urls != self._server_model.server_urls:
                self._server_model.server_urls = new_server_urls
                self._config.clear_cached_data()
        elif server_name != self._server_model.server_name:
            self._server_model.server_urls = server_name
            self._config.clear_cached_data()
        self.back_from_system_settings()

    def system_settings_restore_defaults(self) -> None:
        """Restore system defaults."""
        self._server_model.restore_dev_server_urls()
        self._server_model.server_urls = self._server_model.default_server
        self.back_from_system_settings()

    @Slot()
    def system_settings_server_selected(self, index):
        """Update core and auth line edits."""
        server_name = self._view.ui.systemSettingsServerComboBox.itemData(index)
        if not server_name:
            return

        is_dev = server_name == "dev"
        core_line_edit = self._view.ui.systemSettingsCoreServerLineEdit
        auth_line_edit = self._view.ui.systemSettingsAuthServerLineEdit

        core_line_edit.setEnabled(is_dev)
        auth_line_edit.setEnabled(is_dev)
        if is_dev:
            server_urls = self.system_settings_dev_server_urls
        else:
            server_urls = self._server_model.known_server_urls[server_name]
        core_line_edit.setText(server_urls.core_base_url)
        auth_line_edit.setText(server_urls.oauth_base_url)

    @Slot()
    def system_settings_core_server_edited(self):
        self.system_settings_dev_server_urls.core_base_url = (
            self._view.ui.systemSettingsCoreServerLineEdit.text()
        )

    @Slot()
    def system_settings_auth_server_edited(self):
        self.system_settings_dev_server_urls.oauth_base_url = (
            self._view.ui.systemSettingsAuthServerLineEdit.text()
        )

    ##############################
    # Miscellaneous functionality

    def to_welcome_page(self):
        """Switch to the welcome page."""
        self._view.change_page(self._view.Pages.WELCOME)

    def page_changed(self, index: int):
        """Called when the page of the stacked widget changes"""
        if index == self._view.Pages.LOGIN.value[1]:
            self.handle_login_page()
        elif index == self._view.Pages.WELCOME.value[1]:
            pass
        elif index == self._view.Pages.ADD_CONTROLLER.value[1]:
            self.handle_add_controller_page()
        elif index == self._view.Pages.REPLACE_CONTROLLER.value[1]:
            self.handle_replace_controller_page()
        elif index == self._view.Pages.SYSTEM_SETTINGS.value[1]:
            self.handle_system_settings_page()
        else:
            pass

    def handle_error(self, error: WorkerError):
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
        self._server_model.save_to_config()
        if self._config.config:
            self._config.save_config()
        event.accept()

    def show_help_dialog(self) -> str:
        """Show the help dialog."""
        title = "Help"
        contents = """1. For Snaps (Ubuntu Store) enable serial port access
 - Run in a terminal: snap connect inamata-flasher:raw-usb
 - Restart the app
2. For Snaps (Ubuntu Store) allow saving login (optional)
 - Run in a terminal: snap connect inamata-flasher:password-manager-service
 - Restart the app
3. Additional information and support
 - https://github.com/InamataCo/Flasher
 - https://www.inamata.co"""
        self._view.notify(contents, title, "information")

    def get_found_serial_ports_text(self) -> str:
        """Get the UI text for found serial ports."""
        serial_ports = self._flash_model.get_serial_ports()
        if not serial_ports:
            text = "No serial ports found"
        else:
            text = f"Found {len(serial_ports)} serial port:"
        for port in serial_ports:
            text = text + "\n" if text else text
            text = text + port.device
        return text
