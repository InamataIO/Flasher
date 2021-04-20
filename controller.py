from functools import partial
from os import stat
from wifi_model import DSFlasherWiFiModel
from model import DSFlasherModel
from view import DSFlasherUi


class DSFlasherCtrl:
    def __init__(
        self, model: DSFlasherModel, view: DSFlasherUi, wifi_model: DSFlasherWiFiModel
    ):
        self._model = model
        self._view = view
        self._wifi_model = wifi_model
        model.notify = view.notify
        self.to_welcome_page = partial(self._view.changePage, self._view.Pages.WELCOME)
        self._connectSignals()
        self._connectModelViews()
        view.changePage(view.Pages.LOGIN)

    def _connectSignals(self):
        # Login Page
        self._view.ui.loginButton.clicked.connect(self.log_in)
        # self._view.ui.signUpButton.clicked.connect(self._model.sign_up)
        self._view.ui.signUpButton.clicked.connect(self._view.switch)
        self._view.ui.emailLineEdit.setText(self._model.get_saved_user())
        self._view.ui.emailLineEdit.returnPressed.connect(
            self._view.ui.loginButton.click
        )
        self._view.ui.passwordLineEdit.returnPressed.connect(
            self._view.ui.loginButton.click
        )

        # Welcome Page
        self._view.ui.welcomeLogOutPushButton.clicked.connect(self.log_out)

        # Add Page
        self._view.ui.replaceBackPushButton.clicked.connect(self.to_welcome_page)

        # Replace Page

        # WiFi Page

    def _connectModelViews(self):
        self._view.ui.apListView.setModel(self._wifi_model)
        self._view.ui.addAPListView.setModel(self._wifi_model)

    def log_out(self):
        self._model.log_out()
        self._view.ui.passwordLineEdit.clear()
        self._view.changePage(self._view.Pages.LOGIN)

    def log_in(self):
        success = self._model.log_in(
            self._view.ui.emailLineEdit.text(), self._view.ui.passwordLineEdit.text()
        )
        if success:
            self._view.changePage(self._view.Pages.WELCOME)
            self._view.ui.passwordLineEdit.clear()
