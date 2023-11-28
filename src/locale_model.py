from __future__ import annotations

import logging
from enum import Enum

from PySide6.QtCore import QCoreApplication, QLibraryInfo, QLocale, QTranslator
from PySide6.QtWidgets import QApplication

from config import Config

logger = logging.getLogger()


class LocaleModel:
    class Locale(Enum):
        ENGLISH = ("en_US", "English")
        GERMAN = ("de_DE", "Deutsch")
        FRENCH = ("fr_FR", "Français")
        SPANISH = ("es_ES", "Español")

        def __init__(self, code, label):
            self.code = code
            self.label = label

        @classmethod
        def from_code(cls, code) -> "Locale" | None:
            """Match the complete locale, then try only language."""
            for locale in cls:
                if locale.code == code:
                    return locale
            for locale in cls:
                if locale.code.split("_")[0] == code.split("_")[0]:
                    return locale
            return None

    def __init__(self, config: Config) -> None:
        self._config = config
        self.locale = self._parse_locale(config)
        self.translator: QTranslator | None = None

    @classmethod
    def _parse_locale(cls, config: Config) -> QLocale | None:
        """Parse the saved locale code to a Locale enum."""
        saved_locale = config.config.get("locale")
        if not saved_locale:
            return
        try:
            locale = QLocale(cls.Locale.from_code(saved_locale).code)
        except ValueError as err:
            logger.warning(f"Unknown locale: {err}")
            config.config.pop("locale", None)
            return
        # Ignore generic, C locale
        if locale.country() == QLocale.Country.AnyTerritory:
            return
        return locale

    def translate_app(self, app: QApplication) -> None:
        """Apply translation to the app with the parsed locale."""
        if not self.locale:
            return
        # Set up Qt built-in translations
        translator = QTranslator(app)
        translation_path = QLibraryInfo.path(QLibraryInfo.TranslationsPath)
        if translator.load(self.locale, "qtbase", "_", translation_path):
            app.installTranslator(translator)

        # Set up custom translations
        translator = QTranslator(app)
        translation_path = str(self._config.translations_folder)
        if translator.load(self.locale, "mainwindow", "_", translation_path):
            app.installTranslator(translator)

        translator = QTranslator(app)
        if translator.load(self.locale, "main", "_", translation_path):
            QCoreApplication.instance().installTranslator(translator)

    @classmethod
    def restart_app_message(cls, locale: Locale) -> str:
        match locale:
            case cls.Locale.GERMAN:
                return "Bitte starten Sie die Anwendung neu, um den Sprachwechsel zu übernehmen."
            case cls.Locale.FRENCH:
                return "Veuillez redémarrer l'application pour appliquer le changement de langue."
            case cls.Locale.SPANISH:
                return "Reinicie la aplicación para aplicar el cambio de idioma."
            case _:
                return "Please restart the application to apply the language change."

    @classmethod
    def restart_app_title(cls, locale: Locale) -> str:
        match locale:
            case cls.Locale.GERMAN:
                return "Anwendung neu starten"
            case cls.Locale.FRENCH:
                return "Redémarrer l'application"
            case cls.Locale.SPANISH:
                return "Reiniciar la aplicación"
            case _:
                return "Restart application"
