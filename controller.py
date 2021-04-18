from functools import partial


class DSFlasherCtrl:
    def __init__(self, model, view):
        self._model = model
        self._view = view
        self._connectSignals()

    def _connectSignals(self):
        login_callback = partial(
            self._model.login,
            self._view.ui.emailLineEdit.text,
            self._view.ui.passwordLineEdit.text,
        )
        self._view.ui.loginButton.clicked.connect(login_callback)
        self._view.ui.signUpButton.clicked.connect(self._model.sign_up)
        self._view.ui.emailLineEdit.returnPressed.connect(self._view.ui.loginButton.click)
        self._view.ui.passwordLineEdit.returnPressed.connect(self._view.ui.loginButton.click)
