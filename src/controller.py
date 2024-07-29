import logging
import platform
from typing import Any

from PySide6.QtCore import (
    QCoreApplication,
    QLocale,
    QModelIndex,
    Qt,
    QThreadPool,
    QUrl,
    Slot,
)
from PySide6.QtGui import QCloseEvent, QDesktopServices, QKeySequence, QShortcut
from PySide6.QtWidgets import QComboBox, QMenu, QMessageBox

from about_view import AboutView
from config import BootloaderImageModel, Config, ControllerModel, FirmwareImageModel
from flash_model import FlashModel
from locale_model import LocaleModel
from main_view import MainView
from serial_monitor_controller import SerialMonitorController
from serial_monitor_view import SerialMonitorView
from server_model import ServerModel, WebAppPaths
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
        locale_model: LocaleModel,
        view: MainView,
        config: Config,
        app: QCoreApplication,
    ):
        self._server_model = server_model
        self._flash_model = flash_model
        self._wifi_model = wifi_model
        self._locale_model = locale_model
        self._view = view
        self._config = config
        self._app = app
        # Child objects
        self._about_view: AboutView | None = None
        self._serial_monitor_view: SerialMonitorView | None = None
        self._serial_monitor_controller: SerialMonitorController | None = None
        # Check the user's local permissions once on startup
        self._checked_permissions = False

        self.threadpool = QThreadPool()
        self._connect_model_views()
        self._connect_signals()
        self._connect_shortcuts()
        self._page_after_add_wifi = None
        self._page_before_add_wifi = None
        self._update_wifi_checked_ap = None
        view.change_page(view.Pages.LOGIN)
        # Call login page handler if change_page does not result in a page change
        self.handle_login_page()
        self.auto_log_in()
        self.update_latest_version()

    def _connect_signals(self):
        """Connect widget signals to the appropriate function."""
        self._view.ui.welcomeVersionButton.clicked.connect(self.show_update_modal)
        self._view.ui.loginVersionButton.clicked.connect(self.show_update_modal)

        # Main Application
        self._view.close_callback = self.handle_close
        self._view.ui.stackedWidget.currentChanged.connect(self.page_changed)

        # Login Page
        self._view.ui.loginButton.clicked.connect(self.log_in)
        self._view.ui.signUpButton.clicked.connect(self.sign_up)
        #   Login menus
        self.login_system_menu = QMenu()
        clear_data_label = QCoreApplication.translate("main", "Clear local data")
        self.login_system_menu.addAction(clear_data_label, self.clear_data)
        open_settings_label = QCoreApplication.translate("main", "Open system settings")
        self.login_system_menu.addAction(open_settings_label, self.to_system_settings)
        self._view.ui.loginSystemIconButton.setMenu(self.login_system_menu)
        self.login_locale_menu = QMenu()
        for locale in LocaleModel.Locale:
            self.login_locale_menu.addAction(
                locale.label, lambda i=locale: self.set_locale(i)
            )
        self._view.ui.loginLocaleIconButton.setMenu(self.login_locale_menu)
        self.login_help_menu = QMenu()
        self.login_help_menu.addAction(self.setup_label, self.show_setup_window)
        self.login_help_menu.addAction(AboutView.about_label(), self.show_about_window)
        self._view.ui.loginHelpIconButton.setMenu(self.login_help_menu)

        # Welcome Page
        self._view.ui.welcomeAddControllerButton.clicked.connect(self.to_add_controller)
        self._view.ui.welcomeReplaceControllerButton.clicked.connect(
            self.to_replace_controller
        )
        self._view.ui.welcomeManageWiFiButton.clicked.connect(self.to_manage_wifi)
        self._view.ui.welcomeLogOutPushButton.clicked.connect(self.log_out)
        self.set_welcome_username(self._config.users_name)
        self._view.ui.welcomeOpenWebAppButton.clicked.connect(self.open_web_app)
        self._view.ui.welcomeViewSerialButton.clicked.connect(self.show_serial_window)
        #   Welcome menus
        self.welcome_locale_menu = QMenu()
        for locale in LocaleModel.Locale:
            self.welcome_locale_menu.addAction(
                locale.label, lambda i=locale: self.set_locale(i)
            )
        self._view.ui.welcomeLocaleIconButton.setMenu(self.welcome_locale_menu)
        self.welcome_help_menu = QMenu()
        self.welcome_help_menu.addAction(self.setup_label, self.show_setup_window)
        self.welcome_help_menu.addAction(
            AboutView.about_label(), self.show_about_window
        )
        self._view.ui.welcomeHelpIconButton.setMenu(self.welcome_help_menu)

        # Add Controller Page
        self._view.ui.addControllerControllerTypesComboBox.currentIndexChanged.connect(
            self.add_controller_controller_type_selected
        )
        self._view.ui.addControllerFirmwareVariantsComboBox.currentIndexChanged.connect(
            self.add_controller_firmware_variant_selected
        )
        self._view.ui.addControllerFlashButton.clicked.connect(
            self.add_controller_download_and_flash
        )
        self._view.ui.addControllerReloadButton.clicked.connect(
            self.add_controller_reload
        )
        self._view.ui.addControllerBackButton.clicked.connect(self.to_welcome_page)
        self._view.ui.addControllerDriverButton.clicked.connect(self.to_driver_install)
        self._view.ui.addControllerAPListView.clicked.connect(self.ap_list_clicked)
        self._view.ui.addControllerShowAdvancedButton.stateChanged.connect(
            self.add_controller_show_advanced
        )

        # Replace Controller Page
        self._view.ui.replaceControllerSitesComboBox.currentIndexChanged.connect(
            self.replace_controller_site_selected
        )
        self._view.ui.replaceControllerControllersComboBox.currentIndexChanged.connect(
            self.replace_controller_controller_selected
        )
        self._view.ui.replaceControllerFirmwareVariantsComboBox.currentIndexChanged.connect(
            self.replace_controller_firmware_variant_selected
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
        self._view.ui.replaceControllerAPListView.clicked.connect(self.ap_list_clicked)
        self._view.ui.replaceControllerShowAdvancedButton.stateChanged.connect(
            self.replace_controller_show_advanced
        )

        # Add WiFi Page
        self._view.ui.addWiFiSubmitPushButton.clicked.connect(self.add_wifi_ap)
        self._view.ui.addWiFiBackPushButton.clicked.connect(self.back_from_add_wifi)

        # Update WiFi Page
        self._view.ui.updateWiFiBackPushButton.clicked.connect(
            self.back_from_update_wifi
        )
        self._view.ui.updateWiFiSubmitPushButton.clicked.connect(
            self.update_wifi_ap_details
        )

        # Manage WiFi Page
        self._view.ui.manageWiFiAddButton.clicked.connect(self.manage_wifi_to_add_wifi)
        self._view.ui.manageWiFiRemoveButton.clicked.connect(self.remove_wifi_ap)
        self._view.ui.manageWiFiBackButton.clicked.connect(self.to_welcome_page)
        self._view.ui.manageWiFiEditButton.clicked.connect(
            self.manage_wifi_to_update_wifi
        )
        self._wifi_model.dataChanged.connect(self.manage_wifi_ap_checked)
        self._view.ui.apListView.clicked.connect(self.ap_list_clicked)

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
        self._view.ui.systemSettingsWebAppUrlLineEdit.editingFinished.connect(
            self.system_settings_web_app_url_edited
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
            QUrl("https://github.com/InamataIO/Flasher#driver-setup")
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
        self._check_permissions()

    def log_in(self):
        """Log the user in and save the auth token."""
        self._view.ui.loginLoadingText.show()
        self._view.ui.loginLoadingBar.show()
        self._view.ui.loginSelectedServerText.hide()
        self._view.ui.loginLinkText.show()
        self._view.ui.loginButton.hide()
        self._view.ui.signUpButton.hide()
        worker = Worker(self._server_model.log_in)
        worker.signals.result.connect(self.log_in_result)
        worker.signals.state.connect(self.log_in_display_url)
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

    def log_in_display_url(self, url: str):
        """Show the URL to the web page that should have opened."""
        self._view.ui.loginLinkText.setText(f"{self.open_url_label}\n{url}")

    def log_in_finished(self):
        """After the login attempt, hide the loading widgets."""
        self._view.ui.loginLoadingText.hide()
        self._view.ui.loginLoadingBar.hide()
        self._view.ui.loginLinkText.hide()
        self._view.ui.loginLinkText.setText(self._view.original_login_link_text)
        self._view.ui.loginButton.show()
        self._view.ui.signUpButton.show()
        self._view.ui.loginSelectedServerText.show()

    def log_in_error(self, error):
        """Error handler for the login thread."""
        self.handle_error(error)

    def sign_up(self):
        QDesktopServices.openUrl(QUrl(self._server_model.sign_up_url))

    def clear_data(self):
        self._server_model.restore_dev_server_urls()
        self._server_model.server_urls = self._server_model.default_server
        self._server_model.log_out()
        self._wifi_model.remove_all_aps()
        self._config.clear_stored_data()
        self.handle_login_page()

        self._view.notify(self.clear_local_data_message, self.clear_local_data_title)

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

    def update_latest_version(self):
        worker = Worker(self._server_model.update_newest_version)
        worker.signals.result.connect(self.update_latest_version_result)
        self.threadpool.start(worker)

    def update_latest_version_result(self, version: str):
        """Show the latest available version."""
        if not version:
            logging.warning("Failed fetching latest version tag from GitHub")
            return
        if version == self._config.app_version:
            version_text = (
                version_text
            ) = f"{self._config.app_version} ({self.up_to_date_label})"
        else:
            version_text = (
                f"{self._config.app_version} ({version} {self.available_label})"
            )
        self._view.ui.welcomeVersionButton.setText(version_text)
        self._view.ui.loginVersionButton.setText(version_text)

    def to_system_settings(self):
        """Open select server dialog."""
        self._page_before_system_settings = self._view.current_page()
        self._view.change_page(self._view.Pages.SYSTEM_SETTINGS)

    ############################
    # Welcome Page Functionality

    def handle_welcome_page(self):
        """Check user permissions once."""
        self._check_permissions()

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
        # For the normal user, don't show the server name
        if self._server_model.server_name != "production":
            text = f"{self._server_model.server_name.capitalize()}: {username}"
        else:
            text = username
        self._view.ui.welcomeUsername.setText(text)

    def open_web_app(self, path: Any = "") -> None:
        """Open the browser with the web-app."""
        if not isinstance(path, str):
            path = ""
        url = self._server_model.server_urls.web_app_base_url
        if self._locale_model.locale == QLocale.Language.German:
            url = f"{url}/de/"
        else:
            url = f"{url}/en/"
        QDesktopServices.openUrl(QUrl(url + path))

    def show_serial_window(self) -> None:
        """Show the serial monitor window."""
        self._serial_monitor_view = SerialMonitorView(self._view, self._config)
        self._serial_monitor_controller = SerialMonitorController(
            self._serial_monitor_view, self._config
        )
        self._serial_monitor_view.close_callback = self.clear_serial_monitor
        self._serial_monitor_view.show()

    def clear_serial_monitor(self, event: QCloseEvent) -> None:
        self._serial_monitor_view = None
        self._serial_monitor_controller.close()
        self._serial_monitor_controller = None
        event.accept()

    #############################
    # Add WiFi Page Functionality

    def add_wifi_ap(self):
        """Add the WiFi AP according to the user input (SSID, password)."""
        ssid = self._view.ui.addWiFiSSIDLineEdit.text()
        password = self._view.ui.addWiFiPasswordLineEdit.text()
        if self._is_wifi_ssid_invalid(ssid):
            return
        self._wifi_model.add_ap(ssid, password, True)
        self._view.change_page(self._page_after_add_wifi)
        self._view.ui.addWiFiSSIDLineEdit.clear()
        self._view.ui.addWiFiPasswordLineEdit.clear()

    def _is_wifi_ssid_invalid(self, ssid: str) -> bool:
        if not ssid:
            self._view.notify(
                self.blank_wifi_ssid_message,
                self.invalid_wifi_ssid_title,
                "information",
            )
            return True
        if len(ssid) > 32:
            self._view.notify(
                self.too_long_wifi_ssid_message,
                self.invalid_wifi_ssid_title,
                "information",
            )
            return True
        return False

    def back_from_add_wifi(self):
        """Go to the previous page"""
        if self._page_before_add_wifi:
            self._view.change_page(self._page_before_add_wifi)
            self._page_before_add_wifi = None
        else:
            logging.warning("_page_before_add_wifi was not set")
            self._view.change_page(self._view.Pages.WELCOME)

    ################################
    # Manage WiFi Page Functionality

    def handle_manage_wifi_page(self):
        """Disable edit button until entry selected."""
        self.manage_wifi_ap_checked()

    def manage_wifi_ap_checked(self, *_):
        """Handle selection changed."""
        checked_aps = self._wifi_model.get_checked_aps()
        enable_edit = len(checked_aps) == 1
        self._view.ui.manageWiFiEditButton.setEnabled(enable_edit)
        enable_delete = len(checked_aps) > 0
        self._view.ui.manageWiFiRemoveButton.setEnabled(enable_delete)

    def manage_wifi_to_add_wifi(self):
        self._page_before_add_wifi = self._view.Pages.MANAGE_WIFI
        self._page_after_add_wifi = self._view.Pages.MANAGE_WIFI
        self._view.change_page(self._view.Pages.ADD_WIFI)

    def manage_wifi_to_update_wifi(self):
        checked_aps = self._wifi_model.get_checked_aps()
        self._update_wifi_checked_ap = checked_aps[0]
        self._view.change_page(self._view.Pages.UPDATE_WIFI)

    def remove_wifi_ap(self):
        """Remove the currently selected WiFi AP."""
        self._wifi_model.remove_checked_aps()

    ######################################
    # Update WiFi controller functionality

    def handle_update_wifi_page(self):
        """Populate the line edit fields for the current AP."""
        self._view.ui.updateWiFiSSIDLineEdit.setText(self._update_wifi_checked_ap.ssid)
        self._view.ui.updateWiFiPasswordLineEdit.setText(
            self._update_wifi_checked_ap.password
        )

    def update_wifi_ap_details(self):
        """Update the AP details and go back to the manage page."""
        ssid = self._view.ui.updateWiFiSSIDLineEdit.text()
        if self._is_wifi_ssid_invalid(ssid):
            return
        self._update_wifi_checked_ap.ssid = ssid
        self._update_wifi_checked_ap.password = (
            self._view.ui.updateWiFiPasswordLineEdit.text()
        )
        self._update_wifi_checked_ap = None
        self._view.change_page(self._view.Pages.MANAGE_WIFI)

    def back_from_update_wifi(self):
        """Go back to manage wifi page."""
        self._update_wifi_checked_ap = None
        self._view.change_page(self._view.Pages.MANAGE_WIFI)

    ##############################
    # Add controller functionality

    def handle_add_controller_page(self):
        """Get data and populate the combo boxes on the add controller page."""
        self.add_controller_show_advanced(
            self._view.ui.addControllerShowAdvancedButton.checkState().value
        )
        if self._config.has_cached_sites():
            self.handle_add_controller_page_result(None)
        else:
            self._view.ui.addControllerSerialPortsText.hide()
            self._view.ui.addControllerLoadingText.show()
            self._view.ui.addControllerLoadingBar.show()
            worker = Worker(
                self._server_model.get_static_data,
                controller_type_names=self._config.supported_controller_types,
            )
            worker.signals.result.connect(self.handle_add_controller_page_result)
            worker.signals.error.connect(self.handle_add_controller_page_error)
            worker.signals.finished.connect(self.handle_add_controller_page_finished)
            self.threadpool.start(worker)

    def handle_add_controller_page_result(self, _):
        """Populate the combo boxes with the fetched data for add controller page."""
        # Update the found serial ports
        text = self.get_found_serial_ports_text()
        self._view.ui.addControllerSerialPortsText.setText(text)

        # Update the sites and controller types combo box
        success = self.update_sites_combo_box(self._view.ui.addControllerSitesComboBox)
        if not success:
            return
        success = self.update_controller_types_combo_box(
            self._view.ui.addControllerControllerTypesComboBox
        )
        if not success:
            return

    def handle_add_controller_page_error(self, error):
        """Error handler for the add controller data fetch thread."""
        self.handle_error(error)

    def handle_add_controller_page_finished(self):
        """Hide the loading widgets for the add controller page."""
        self._view.ui.addControllerLoadingText.hide()
        self._view.ui.addControllerLoadingBar.hide()
        self._view.ui.addControllerSerialPortsText.show()

    def add_controller_controller_type_selected(self, index):
        self.add_controller_update_firmware_variants_field()

    def add_controller_firmware_variant_selected(self, index):
        self.add_controller_update_firmware_version_field()

    def add_controller_update_firmware_variants_field(self):
        current_controller_type: str = (
            self._view.ui.addControllerControllerTypesComboBox.currentData()
        )
        if not current_controller_type:
            return
        firmware_variants_combo: QComboBox = (
            self._view.ui.addControllerFirmwareVariantsComboBox
        )
        firmware_variants_combo.clear()
        for i in self._config.get_firmware_variants_for_controller_type(
            current_controller_type
        ):
            firmware_variants_combo.addItem(i.name, userData=i.id)
        if not firmware_variants_combo.count():
            self._view.notify(
                self.no_firmware_variants_found_message,
                self.no_firmware_variants_found_title,
            )

    def add_controller_update_firmware_version_field(self):
        """Query server for firmware for the selected controller type."""
        firmware_variant_id: str | None = (
            self._view.ui.addControllerFirmwareVariantsComboBox.currentData()
        )
        if not firmware_variant_id:
            return
        firmware_variant = self._config.get_firmware_variant(firmware_variant_id)
        if firmware_variant and not firmware_variant.firmware_image_ids:
            worker = Worker(
                self._server_model.get_firmware_data,
                firmware_variant_id=firmware_variant_id,
            )
            worker.signals.result.connect(
                self.add_controller_update_firmware_version_field_result
            )
            worker.signals.error.connect(
                self.add_controller_update_firmware_version_field_error
            )
            worker.signals.finished.connect(self.handle_add_controller_page_finished)
            self.threadpool.start(worker)
            return
        self.add_controller_update_firmware_version_field_result()

    def add_controller_update_firmware_version_field_result(self):
        firmware_variant_id = (
            self._view.ui.addControllerFirmwareVariantsComboBox.currentData()
        )
        firmware_versions_combo: QComboBox = (
            self._view.ui.addControllerFirmwareVersionsComboBox
        )
        firmware_versions_combo.blockSignals(True)
        firmware_versions_combo.clear()
        for i in self._config.get_firmware_images_for_variant(firmware_variant_id):
            firmware_versions_combo.addItem(str(i.version), userData=i.id)
        firmware_versions_combo.blockSignals(False)
        firmware_versions_combo.currentIndexChanged.emit(0)

    def add_controller_update_firmware_version_field_error(self, error):
        self.handle_error(error)

    def add_controller_reload(self):
        """Clear the cached data and repopulate the combo boxes."""
        self._config.clear_cached_data()
        self.handle_add_controller_page()

    def add_controller_download_and_flash(self):
        """Download the selected firmware image and flash it to the ESP."""
        if not self.add_controller_is_flash_input_valid():
            return
        self._view.ui.addControllerProgressText.setText(
            f"{self.get_firmware_label} (1/4)"
        )
        self.add_controller_set_widgets_for_flashing(True)

        firmware_image_id = (
            self._view.ui.addControllerFirmwareVersionsComboBox.currentData()
        )
        worker = Worker(self._server_model.download_firmware_image, firmware_image_id)
        worker.signals.progress.connect(self.add_controller_download_firmware_progress)
        worker.signals.result.connect(self.add_controller_download_firmware_result)
        worker.signals.error.connect(self.add_controller_download_firmware_error)
        self.threadpool.start(worker)

    def add_controller_is_flash_input_valid(self):
        """Checks the user input and returns true if it looks good."""
        if not self._view.ui.addControllerSitesComboBox.currentData():
            self._view.notify(self.missing_site_message, self.missing_input_title)
            return False
        if not self._view.ui.addControllerNameLineEdit.text():
            self._view.notify(self.missing_name_message, self.missing_input_title)
            return False
        if not self._wifi_model.get_checked_aps():
            self._view.notify(self.missing_wifi_message, self.missing_input_title)
            return False
        if not self._view.ui.addControllerFirmwareVersionsComboBox.currentData():
            self._view.notify(self.missing_firmware_message, self.missing_input_title)
            return False
        return True

    def add_controller_download_firmware_progress(self, progress):
        """Set the download progress for 0% to 30%."""
        mapped_progress = progress / 100 * 30
        self.add_controller_set_progress_bar(mapped_progress)

    def add_controller_download_firmware_result(self, firmware: FirmwareImageModel):
        """After completing the download, flash the controller."""
        self._view.ui.addControllerProgressText.setText(
            f"{self.get_bootloader_label} (2/4)"
        )
        self.add_controller_set_progress_bar(30)

        bootloader = self._config.get_bootloader_image(firmware.bootloader_image_id)
        if not bootloader:
            return self.add_controller_download_bootloader_result(bootloader)
        worker = Worker(self._server_model.download_bootloader_image, bootloader.id)
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

    def add_controller_download_bootloader_result(
        self, bootloader: BootloaderImageModel
    ):
        """After completing the bootloader download, register the controller."""
        self._view.ui.addControllerProgressText.setText(
            f"{self.registering_label} (3/4)"
        )
        self.add_controller_set_progress_bar(40)

        name = self._view.ui.addControllerNameLineEdit.text()
        site_id = self._view.ui.addControllerSitesComboBox.currentData()
        controller_type_id = (
            self._view.ui.addControllerControllerTypesComboBox.currentData()
        )
        firmware_image_id = (
            self._view.ui.addControllerFirmwareVersionsComboBox.currentData()
        )

        worker = Worker(
            self._server_model.register_controller,
            name,
            site_id,
            controller_type_id,
            firmware_image_id,
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
        self._view.ui.addControllerProgressText.setText(f"{self.flashing_label} (4/4)")
        self.add_controller_set_progress_bar(50)

        if platform.system() == "Windows":
            self._view.notify(self.flash_mode_message, self.flash_mode_title)

        # Start a task to flash the controller
        wifi_aps = self._wifi_model.get_checked_aps()
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
        msg_box = QMessageBox(
            QMessageBox.Icon.Information,
            self.flash_succeeded_title,
            self.flash_succeeded_message,
            parent=self._view.ui,
        )
        setup_button = msg_box.addButton(
            self.setup_peripherals_label, QMessageBox.ButtonRole.HelpRole
        )
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()

        if msg_box.clickedButton() == setup_button:
            self.open_web_app(WebAppPaths.devices_peripherals)

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
        self._view.ui.addControllerControllerTypesComboBox.setDisabled(is_flashing)
        self._view.ui.addControllerFirmwareVariantsComboBox.setDisabled(is_flashing)
        self._view.ui.addControllerFirmwareVersionsComboBox.setDisabled(is_flashing)
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

    def add_controller_show_advanced(self, state: int):
        """Callback when the show advanced checkbox is pressed."""
        if state == Qt.CheckState.Checked.value:
            self._view.ui.addControllerFirmwareLabel.show()
            self._view.ui.addControllerFirmwareVariantsComboBox.show()
            self._view.ui.addControllerFirmwareVersionsComboBox.show()
        elif state == Qt.CheckState.Unchecked.value:
            self._view.ui.addControllerFirmwareLabel.hide()
            self._view.ui.addControllerFirmwareVariantsComboBox.hide()
            self._view.ui.addControllerFirmwareVersionsComboBox.hide()

    #######################################
    # Replace Controller Page Functionality

    def handle_replace_controller_page(self):
        """Fetch data and populate the combo boxes for the replace controller page."""
        self.replace_controller_show_advanced(
            self._view.ui.replaceControllerShowAdvancedButton.checkState().value
        )
        if self._config.has_cached_sites():
            self.handle_replace_controller_page_result(None)
        else:
            self._view.ui.replaceControllerSerialPortsText.hide()
            self._view.ui.replaceControllerLoadingText.show()
            self._view.ui.replaceControllerLoadingBar.show()
            worker = Worker(
                self._server_model.get_static_data,
                controller_type_names=self._config.supported_controller_types,
            )
            worker.signals.result.connect(self.handle_replace_controller_page_result)
            worker.signals.error.connect(self.handle_replace_controller_page_error)
            worker.signals.finished.connect(
                self.handle_replace_controller_page_finished
            )
            self.threadpool.start(worker)

    def handle_replace_controller_page_result(self, _):
        """Populate the combo boxes excl. controllers for the replace controller page."""
        # Update the found serial ports
        text = self.get_found_serial_ports_text()
        self._view.ui.replaceControllerSerialPortsText.setText(text)

        # Update the site combo box and retain the currently selected item
        sites_combo: QComboBox = self._view.ui.replaceControllerSitesComboBox
        success = self.update_sites_combo_box(sites_combo)
        if not success:
            return

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
        self.replace_controller_site_selected(0)
        self.handle_replace_controller_page()

    def replace_controller_site_selected(self, index):
        """Start the process to populate the controller combo box for the selected site."""
        if site_id := self._view.ui.replaceControllerSitesComboBox.itemData(index):
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
        self, controllers: dict[str, ControllerModel]
    ):
        """Populate the controller combo box with the fetched data."""
        self.populate_replace_controller_controllers(list(controllers.values()))

    def replace_controller_load_controllers_error(self, error):
        """Error handler for fetching the controllers thread."""
        self.handle_error(error)

    def replace_controller_load_controllers_finished(self):
        """Hide the loading widgets on the replace controller page."""
        self._view.ui.replaceControllerLoadingText.hide()
        self._view.ui.replaceControllerLoadingBar.hide()
        self._view.ui.replaceControllerSerialPortsText.show()

    def replace_controller_controller_selected(self, index):
        self.replace_controller_update_firmware_variants_field()

    def replace_controller_firmware_variant_selected(self, index):
        self.replace_controller_update_firmware_version_field()

    def replace_controller_update_firmware_variants_field(self):
        controller = self._config.get_controller(
            self._view.ui.replaceControllerControllersComboBox.currentData()
        )
        if not controller:
            return
        firmware_image = self._config.get_firmware_image(controller.firmware_image_id)
        if not firmware_image:
            return

        firmware_variants_combo: QComboBox = (
            self._view.ui.replaceControllerFirmwareVariantsComboBox
        )
        firmware_variants_combo.blockSignals(True)
        firmware_variants_combo.clear()
        for i in self._config.get_firmware_variants_for_controller_type(
            controller.controller_type_id
        ):
            firmware_variants_combo.addItem(i.name, userData=i.id)
        firmware_variants_combo.blockSignals(False)
        if not firmware_variants_combo.count():
            self._view.notify(
                self.no_firmware_variants_found_message,
                self.no_firmware_variants_found_title,
            )

        # Set the variant to that currently on the controller
        index = firmware_variants_combo.findData(firmware_image.firmware_variant_id)
        if index >= 0:
            firmware_variants_combo.setCurrentIndex(index)
        else:
            firmware_variants_combo.currentIndexChanged.emit(0)

    def populate_replace_controller_controllers(
        self, controllers: list[ControllerModel]
    ) -> None:
        """Populate the controller combo box for the selected site."""
        controllers_combo: QComboBox = (
            self._view.ui.replaceControllerControllersComboBox
        )
        current_controller = controllers_combo.currentData()
        controllers.sort(key=lambda c: c.name)

        # Block signals until setting the current index. Otherwise the controller
        # combo box is activated multiple times.
        controllers_combo.blockSignals(True)
        controllers_combo.clear()
        for i in controllers:
            controllers_combo.addItem(i.name, userData=i.id)
        controllers_combo.blockSignals(False)
        if not controllers:
            controllers_combo.addItem(self.no_controllers_found_label)
            return

        # Retain the currently selected item
        index = controllers_combo.findData(current_controller)
        if index >= 0:
            controllers_combo.setCurrentIndex(index)
        else:
            controllers_combo.currentIndexChanged.emit(0)

    def replace_controller_update_firmware_version_field(self):
        """Query server for firmware for the selected controller type."""
        firmware_variant_id: str | None = (
            self._view.ui.replaceControllerFirmwareVariantsComboBox.currentData()
        )
        if not firmware_variant_id:
            return
        firmware_variant = self._config.get_firmware_variant(firmware_variant_id)
        if firmware_variant and not firmware_variant.firmware_image_ids:
            worker = Worker(
                self._server_model.get_firmware_data,
                firmware_variant_id=firmware_variant_id,
            )
            worker.signals.result.connect(
                self.replace_controller_update_firmware_version_field_result
            )
            worker.signals.error.connect(
                self.replace_controller_update_firmware_version_field_error
            )
            worker.signals.finished.connect(
                self.handle_replace_controller_page_finished
            )
            self.threadpool.start(worker)
            return
        self.replace_controller_update_firmware_version_field_result()

    def replace_controller_update_firmware_version_field_result(self):
        firmware_variant_id = (
            self._view.ui.replaceControllerFirmwareVariantsComboBox.currentData()
        )
        firmware_images_combo: QComboBox = (
            self._view.ui.replaceControllerFirmwareVersionsComboBox
        )
        firmware_images_combo.blockSignals(True)
        firmware_images_combo.clear()
        for i in self._config.get_firmware_images_for_variant(firmware_variant_id):
            firmware_images_combo.addItem(str(i.version), userData=i.id)
        firmware_images_combo.blockSignals(False)
        firmware_images_combo.currentIndexChanged.emit(0)

    def replace_controller_update_firmware_version_field_error(self, error):
        self.handle_error(error)

    def replace_controller_download_and_flash(self):
        """Download the selected firmware image and flash it to the ESP."""
        if not self.replace_controller_is_flash_input_valid():
            return
        self._view.ui.replaceControllerProgressText.setText(
            f"{self.get_firmware_label} (1/4)"
        )
        self.replace_controller_set_widgets_for_flashing(True)

        firmware_image_id = (
            self._view.ui.replaceControllerFirmwareVersionsComboBox.currentData()
        )
        worker = Worker(self._server_model.download_firmware_image, firmware_image_id)
        worker.signals.progress.connect(
            self.replace_controller_download_firmware_progress
        )
        worker.signals.result.connect(self.replace_controller_download_firmware_result)
        worker.signals.error.connect(self.replace_controller_download_firmware_error)
        self.threadpool.start(worker)

    def replace_controller_is_flash_input_valid(self) -> bool:
        """Checks the user input and returns true is it looks good."""
        if not self._view.ui.replaceControllerSitesComboBox.currentData():
            self._view.notify(self.missing_site_message, self.missing_input_title)
            return False
        if not self._view.ui.replaceControllerControllersComboBox.currentData():
            self._view.notify(self.missing_controller_message, self.missing_input_title)
            return False
        if not self._wifi_model.get_checked_aps():
            self._view.notify(self.missing_wifi_message, self.missing_input_title)
            return False
        if not self._view.ui.replaceControllerFirmwareVersionsComboBox.currentData():
            self._view.notify(self.missing_firmware_message, self.missing_input_title)
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
        self._view.ui.replaceControllerFirmwareVariantsComboBox.setDisabled(is_flashing)
        self._view.ui.replaceControllerFirmwareVersionsComboBox.setDisabled(is_flashing)
        self._view.ui.replaceControllerFlashButton.setDisabled(is_flashing)
        self._view.ui.replaceControllerReloadButton.setDisabled(is_flashing)
        self._view.ui.replaceControllerBackButton.setDisabled(is_flashing)

    def replace_controller_download_firmware_progress(self, progress):
        """Set download progress for 0% to 30%."""
        mapped_progress = progress / 100 * 30
        self.replace_controller_set_progress_bar(mapped_progress)

    def replace_controller_download_firmware_result(self, firmware: FirmwareImageModel):
        """After completing the download, flash the controller."""
        self._view.ui.replaceControllerProgressText.setText(
            f"{self.get_bootloader_label} (2/4)"
        )
        self.replace_controller_set_progress_bar(30)

        bootloader = self._config.get_bootloader_image(firmware.bootloader_image_id)
        if not bootloader:
            return self.replace_controller_download_bootloader_result({})
        worker = Worker(self._server_model.download_bootloader_image, bootloader.id)
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

    def replace_controller_download_bootloader_result(
        self, bootloader_image: BootloaderImageModel
    ):
        """After completing the download, flash the controller."""
        self._view.ui.replaceControllerProgressText.setText(
            f"{self.registering_label} (3/4)"
        )
        self._view.ui.replaceControllerProgressBar.setValue(40)

        controller_id = self._view.ui.replaceControllerControllersComboBox.currentData()
        controller = self._config.get_controller(controller_id)
        if not controller:
            self._view.notify(
                self.missing_controller_message, self.missing_cache_title, "critical"
            )
            return
        controller.firmware_image_id = (
            self._view.ui.replaceControllerFirmwareVersionsComboBox.currentData()
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
        self._view.ui.replaceControllerProgressText.setText(
            f"{self.flashing_label} (4/4)"
        )
        self._view.ui.replaceControllerProgressBar.setValue(50)

        # Notify the user to hold the flash (boot) button
        if platform.system() == "Windows":
            self._view.notify(self.flash_mode_message, self.flash_mode_title)

        # Start a task to flash the controller
        wifi_aps = self._wifi_model.get_checked_aps()
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
        """Displays that flashing has succeeded."""
        msg_box = QMessageBox(
            QMessageBox.Icon.Information,
            self.flash_succeeded_title,
            self.flash_succeeded_message,
            parent=self._view.ui,
        )
        setup_button = msg_box.addButton(
            self.setup_peripherals_label, QMessageBox.ButtonRole.HelpRole
        )
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()

        if msg_box.clickedButton() == setup_button:
            self.open_web_app(WebAppPaths.devices_peripherals)

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

    def replace_controller_show_advanced(self, state: int):
        """Callback when the show advanced checkbox is pressed."""
        if state == Qt.CheckState.Checked.value:
            self._view.ui.replaceControllerFirmwareLabel.show()
            self._view.ui.replaceControllerFirmwareVariantsComboBox.show()
            self._view.ui.replaceControllerFirmwareVersionsComboBox.show()
        elif state == Qt.CheckState.Unchecked.value:
            self._view.ui.replaceControllerFirmwareLabel.hide()
            self._view.ui.replaceControllerFirmwareVariantsComboBox.hide()
            self._view.ui.replaceControllerFirmwareVersionsComboBox.hide()

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
            logging.warning("_page_before_system_settings was not set")
            self._view.change_page(self._view.Pages.LOGIN)

    def system_settings_save(self):
        """Save server settings."""
        index = self._view.ui.systemSettingsServerComboBox.currentIndex()
        server_name = self._view.ui.systemSettingsServerComboBox.itemData(index)
        if server_name == self._server_model.dev_server_name:
            new_server_urls = ServerModel.ServerUrls(
                core_base_url=self._view.ui.systemSettingsCoreServerLineEdit.text(),
                oauth_base_url=self._view.ui.systemSettingsAuthServerLineEdit.text(),
                web_app_base_url=self._view.ui.systemSettingsWebAppUrlLineEdit.text(),
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
        web_app_line_edit = self._view.ui.systemSettingsWebAppUrlLineEdit

        core_line_edit.setEnabled(is_dev)
        auth_line_edit.setEnabled(is_dev)
        web_app_line_edit.setEnabled(is_dev)
        if is_dev:
            server_urls = self.system_settings_dev_server_urls
        else:
            server_urls = self._server_model.known_server_urls[server_name]
        core_line_edit.setText(server_urls.core_base_url)
        auth_line_edit.setText(server_urls.oauth_base_url)
        web_app_line_edit.setText(server_urls.web_app_base_url)

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

    @Slot()
    def system_settings_web_app_url_edited(self):
        self.system_settings_dev_server_urls.web_app_base_url = (
            self._view.ui.systemSettingsWebAppUrlLineEdit.text()
        )

    ##############################
    # Miscellaneous functionality

    def set_locale(self, locale: LocaleModel.Locale):
        self._config.config["locale"] = locale.code
        self._view.notify(
            self._locale_model.restart_app_message(locale),
            self._locale_model.restart_app_title(locale),
        )

    def to_welcome_page(self):
        """Switch to the welcome page."""
        self._view.change_page(self._view.Pages.WELCOME)

    def page_changed(self, index: int) -> None:
        """Called when the page of the stacked widget changes"""
        if index == self._view.Pages.LOGIN.value[1]:
            self.handle_login_page()
        elif index == self._view.Pages.WELCOME.value[1]:
            self.handle_welcome_page()
        elif index == self._view.Pages.MANAGE_WIFI.value[1]:
            self.handle_manage_wifi_page()
        elif index == self._view.Pages.UPDATE_WIFI.value[1]:
            self.handle_update_wifi_page()
        elif index == self._view.Pages.ADD_CONTROLLER.value[1]:
            self.handle_add_controller_page()
        elif index == self._view.Pages.REPLACE_CONTROLLER.value[1]:
            self.handle_replace_controller_page()
        elif index == self._view.Pages.SYSTEM_SETTINGS.value[1]:
            self.handle_system_settings_page()

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

    def show_setup_window(self) -> None:
        """Show the help window."""
        if self._config.is_snap:
            contents = self.snap_help
        elif platform.system() == "Linux":
            contents = self.linux_help
        else:
            contents = self.windows_help
        self._view.notify(contents, self.setup_label, "information")

    def show_about_window(self) -> None:
        """Show the about window."""
        self._about_view = AboutView(self._view, self._config)
        self._about_view.close_callback = self.clear_about_window
        self._about_view.show()

    def clear_about_window(self, event: QCloseEvent) -> None:
        self._about_view = None
        event.accept()

    def show_update_modal(self) -> None:
        """Show the update modal window."""
        latest_version = self._server_model.github_latest_version
        if not latest_version:
            self._view.notify(
                self.update_modal_error_message,
                self.update_modal_error_title,
                "warning",
            )
            return
        if latest_version == self._config.app_version:
            self._view.notify(
                self.update_modal_up_to_date_message,
                self.update_modal_up_to_date_title,
                "information",
            )
            return
        if self._config.is_snap:
            self._view.notify(
                self.update_modal_snap_message,
                self.update_modal_snap_title,
                "information",
            )
            return
        msg_box = QMessageBox(self._view.ui)
        msg_box.setWindowTitle(self.update_modal_available_title)
        msg_box.setText(self.update_modal_available_message)
        download_button = msg_box.addButton(
            self.update_modal_download_label, QMessageBox.ButtonRole.ActionRole
        )
        show_release_button = msg_box.addButton(
            self.update_modal_show_release_label, QMessageBox.ButtonRole.HelpRole
        )
        msg_box.addButton(QMessageBox.StandardButton.Close)
        msg_box.exec()

        if msg_box.clickedButton() == download_button:
            if platform.system() == "Linux":
                url = self._server_model.github_linux_download_url
            else:
                url = self._server_model.github_windows_download_url
            QDesktopServices.openUrl(QUrl(url))
        elif msg_box.clickedButton() == show_release_button:
            QDesktopServices.openUrl(QUrl(self._server_model.github_latest_release_url))

    def _check_permissions(self) -> None:
        """Run the permission checks."""
        if self._checked_permissions:
            return
        self._checked_permissions = True
        worker = Worker(self._flash_model.check_permissions)
        worker.signals.result.connect(self._handle_check_permissions_result)
        self.threadpool.start(worker)

    def _handle_check_permissions_result(self, error: str) -> None:
        if error:
            self._view.notify(error, self.permission_error_title, "warning")

    def get_found_serial_ports_text(self) -> str:
        """Get the UI text for found serial ports."""
        serial_ports = self._flash_model.get_serial_ports()
        text = self.found_serial_port_label(len(serial_ports))
        for port in serial_ports:
            text = text + "\n" if text else text
            text = text + port.device
        return text

    def ap_list_clicked(self, index: QModelIndex):
        self._wifi_model.toggle_checked(index)

    def update_sites_combo_box(self, sites_combo: QComboBox) -> bool:
        """Updates the sites combo box, returns true if one was set."""
        current_site = sites_combo.currentData()

        # Block signals until setting the current index. Otherwise the controller
        # combo box is activated multiple times.
        sites_combo.blockSignals(True)
        sites_combo.clear()
        for i in self._config.get_sites():
            sites_combo.addItem(i.name, userData=i.id)
        sites_combo.blockSignals(False)
        if not sites_combo.count():
            sites_combo.addItem(self.no_sites_found_title)
            self._view.notify(self.no_sites_found_message, self.no_sites_found_title)
            return False

        # Retain the currently selected item
        index = sites_combo.findData(current_site)
        if index >= 0:
            sites_combo.setCurrentIndex(index)
        else:
            sites_combo.currentIndexChanged.emit(0)
        return True

    def update_controller_types_combo_box(
        self, controller_types_combo: QComboBox
    ) -> bool:
        """Updates the controller types combo box, returns true if one was set."""
        current_controller_type: str = controller_types_combo.currentData()

        # Block signals until setting the current index. Otherwise the controller
        # combo box is activated multiple times.
        controller_types_combo.blockSignals(True)
        controller_types_combo.clear()
        for i in self._config.get_controller_types():
            controller_types_combo.addItem(i.name, userData=i.id)
        controller_types_combo.blockSignals(False)
        if not controller_types_combo.count():
            controller_types_combo.addItem(self.no_controller_types_found_title)
            self._view.notify(
                self.no_controller_types_found_message,
                self.no_controller_types_found_title,
            )
            return False

        # Retain the currently selected item
        index = controller_types_combo.findData(current_controller_type)
        if index >= 0:
            controller_types_combo.setCurrentIndex(index)
        else:
            controller_types_combo.currentIndexChanged.emit(0)
        return True

    ##############################
    # Translated text

    @property
    def about_label(self) -> str:
        return QCoreApplication.translate("main", "About")

    @property
    def setup_label(self) -> str:
        return QCoreApplication.translate("main", "Setup")

    @property
    def open_url_label(self) -> str:
        return QCoreApplication.translate(
            "main", "Open the following web page if it does not automatically open."
        )

    @property
    def clear_local_data_title(self) -> str:
        return QCoreApplication.translate("main", "Cleared local data")

    @property
    def clear_local_data_message(self) -> str:
        return QCoreApplication.translate(
            "main", "Cleared secrets, configurations and cached data."
        )

    @property
    def invalid_wifi_ssid_title(self) -> str:
        return QCoreApplication.translate("main", "Invalid WiFi connection")

    @property
    def blank_wifi_ssid_message(self) -> str:
        return QCoreApplication.translate(
            "main", "The WiFi name (SSID) is blank. Please enter a WiFi name."
        )

    @property
    def too_long_wifi_ssid_message(self) -> str:
        return QCoreApplication.translate(
            "main",
            "The WiFi name (SSID) is too long. Please enter a WiFi name with 32 characters or fewer.",
        )

    @property
    def latest_label(self) -> str:
        return QCoreApplication.translate(
            "main", "Latest", "Label for latest firmware image"
        )

    @property
    def no_firmware_images_found_message(self) -> str:
        return QCoreApplication.translate(
            "main",
            "No firmware images found on the server. Check that you have permissions to view firmware images or contact support.",
        )

    @property
    def no_firmware_images_found_title(self) -> str:
        return QCoreApplication.translate("main", "No firmware images found")

    @property
    def no_firmware_images_found_label(self) -> str:
        return QCoreApplication.translate("main", "No firmware images found")

    @property
    def flash_mode_title(self) -> str:
        return QCoreApplication.translate("main", "Enable Flash Mode")

    @property
    def flash_mode_message(self) -> str:
        return QCoreApplication.translate(
            "main",
            "After closing this message, please press and hold the boot button on the ESP32 until the flash process starts.",
        )

    @property
    def flash_succeeded_title(self) -> str:
        return QCoreApplication.translate("main", "Finished Flashing")

    @property
    def flash_succeeded_message(self) -> str:
        return QCoreApplication.translate(
            "main", "Successfully flashed the microcontroller"
        )

    @property
    def setup_peripherals_label(self) -> str:
        return QCoreApplication.translate("main", "Setup peripherals")

    @property
    def no_sites_found_title(self) -> str:
        return QCoreApplication.translate("main", "No Sites Found")

    @property
    def no_sites_found_message(self) -> str:
        return QCoreApplication.translate(
            "main", "No sites found. Use the web app to create new sites."
        )

    @property
    def no_controller_types_found_title(self) -> str:
        return QCoreApplication.translate("main", "No controller types found")

    @property
    def no_controller_types_found_message(self) -> str:
        return QCoreApplication.translate(
            "main",
            "No controller types found. Use the web app to create new controller types.",
        )

    @property
    def no_controllers_found_label(self) -> str:
        return QCoreApplication.translate("main", "No controllers found")

    @property
    def missing_cache_title(self) -> str:
        return QCoreApplication.translate("main", "Missing cached data")

    @property
    def missing_controller_message(self) -> str:
        return QCoreApplication.translate(
            "main",
            "Controller not found in cache. Please clear cached data and try again.",
        )

    @property
    def get_firmware_label(self) -> str:
        return QCoreApplication.translate("main", "Get Firmware")

    @property
    def get_bootloader_label(self) -> str:
        return QCoreApplication.translate("main", "Get Bootloader")

    @property
    def registering_label(self) -> str:
        return QCoreApplication.translate("main", "Registering")

    @property
    def flashing_label(self) -> str:
        return QCoreApplication.translate("main", "Flashing")

    @property
    def missing_input_title(self) -> str:
        return QCoreApplication.translate("main", "Missing Input")

    @property
    def missing_site_message(self) -> str:
        return QCoreApplication.translate(
            "main",
            "Please select a site or reload if none are available."
            " If the problem persists please update the Inamata Flasher or contact your administrator.",
        )

    @property
    def missing_name_message(self) -> str:
        return QCoreApplication.translate(
            "main", "Please enter a name for the new controller."
        )

    @property
    def missing_wifi_message(self) -> str:
        return QCoreApplication.translate(
            "main",
            "Please select one or more WiFi connections to be used by the controller."
            " To add or change entries, go to the 'Manage WiFi' page.",
        )

    @property
    def missing_firmware_message(self) -> str:
        return QCoreApplication.translate(
            "main",
            "Please select a firmware version or reload if none are available."
            " If the problem persists please update the Inamata Flasher or contact your administrator.",
        )

    @property
    def permission_error_title(self) -> str:
        return QCoreApplication.translate("main", "Permission error")

    def found_serial_port_label(self, n: int) -> str:
        if not n:
            return QCoreApplication.translate("main", "No serial ports found")
        if n == 1:
            return QCoreApplication.translate("main", "Found 1 serial port:")
        return QCoreApplication.translate("main", "Found %n serial ports:", "", n)

    @property
    def available_label(self) -> str:
        return QCoreApplication.translate("main", "available")

    @property
    def up_to_date_label(self) -> str:
        return QCoreApplication.translate("main", "up to date")

    @property
    def update_modal_available_title(self) -> str:
        return QCoreApplication.translate("main", "New version avaiable")

    @property
    def update_modal_available_message(self) -> str:
        return QCoreApplication.translate(
            "main",
            "A newer version of the Flasher is available. Update to avoid inconsistent behavior and receive bug fixes. Download the installer directly or view the release notes first.",
        )

    @property
    def update_modal_up_to_date_title(self) -> str:
        return QCoreApplication.translate("main", "Flasher is up-to-date")

    @property
    def update_modal_up_to_date_message(self) -> str:
        return QCoreApplication.translate(
            "main", "You already have the latest version of the Flasher."
        )

    @property
    def update_modal_error_title(self) -> str:
        return QCoreApplication.translate("main", "Fetching newest version failed")

    @property
    def update_modal_error_message(self) -> str:
        return QCoreApplication.translate(
            "main",
            "There was a connection error trying to fetch the latest version details.",
        )

    @property
    def update_modal_download_label(self) -> str:
        return QCoreApplication.translate("main", "Download")

    @property
    def update_modal_show_release_label(self) -> str:
        return QCoreApplication.translate("main", "Show release")

    @property
    def update_modal_snap_title(self) -> str:
        return QCoreApplication.translate("main", "Automatic updates")

    @property
    def update_modal_snap_message(self) -> str:
        return QCoreApplication.translate(
            "main",
            "The Flasher is installed as a Snap and will automatically be updated in a few days.",
        )

    @property
    def snap_help(self) -> str:
        return QCoreApplication.translate(
            "help",
            """1. Enable serial port access (part 1)
  - Run in a terminal: sudo usermod -a -G dialout $USER

2. Log out and back in again (or restart)

3. Enable serial port access (part 2)
 - Run in a terminal: snap connect inamata-flasher:raw-usb
 - Restart the app

4. (Optional) Allow saving login
 - Run in a terminal: snap connect inamata-flasher:password-manager-service
 - Restart the app

5. (Optional) Verify permissions
 - Run in a terminal: snap connections inamata-flasher
 - Run in a terminal: groups

6. Additional information and support
 - https://github.com/InamataIO/Flasher
 - https://www.inamata.io/forum/""",
        )

    @property
    def linux_help(self) -> str:
        return QCoreApplication.translate(
            "help",
            """1. Enable serial port access
  - Run in a terminal: sudo usermod -a -G dialout $USER

2. Log out and back in again (or restart)

3. (Optional) Verify permissions
 - Run in a terminal: groups

4. Additional information and support
 - https://github.com/InamataIO/Flasher
 - https://www.inamata.io/forum/""",
        )

    @property
    def windows_help(self) -> str:
        return QCoreApplication.translate(
            "help",
            """1. Install the serial driver (CP210x)
  - https://www.silabs.com/documents/public/software/CP210x_Windows_Drivers.zip
  - https://github.com/InamataIO/Flasher#driver-setup

2. Additional information and support
 - https://github.com/InamataIO/Flasher
 - https://www.inamata.io/forum/""",
        )
