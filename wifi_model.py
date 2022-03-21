from typing import List

from PySide2 import QtCore
from PySide2.QtCore import QAbstractListModel, QModelIndex

from config import Config


class WiFiModel(QAbstractListModel):
    class AP:
        def __init__(self, ssid, password):
            self.ssid: str = ssid
            self.password: str = password

        def __str__(self):
            return f"{self.ssid}:{self.password}"

    def __init__(self, config: Config, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._config = config
        self.aps: List[self.AP] = []
        ap_config = config.config.get("wifi_aps", [])
        new_aps = [self.AP(ssid=i["ssid"], password=i["password"]) for i in ap_config]
        self.aps.extend(new_aps)

    def data(self, index: QModelIndex, role) -> str:
        if role == QtCore.Qt.DisplayRole:
            ap = self.aps[index.row()]
            return str(ap)

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.aps)

    def ap_count(self):
        return len(self.aps)

    def add_ap(self, ssid, password):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        # Remove existing AP if it has the same SSID
        new_aps = [i for i in self.aps if i.ssid != ssid]
        new_aps.append(self.AP(ssid=ssid, password=password))
        self.aps = new_aps
        self.endInsertRows()

    def remove_ap(self, row):
        self.beginRemoveRows(QModelIndex(), row, row)
        self.aps.pop(row)
        self.endRemoveRows()

    def remove_all_aps(self):
        self.aps = []
        self._config.config.pop("wifi_aps")

    def get_ap(self, index: QModelIndex):
        """Get the AP at the specified index."""
        return self.aps[index.row()]

    def save_to_config(self):
        """Save the current APs to the config"""
        wifi_aps = [{"ssid": i.ssid, "password": i.password} for i in self.aps]
        if wifi_aps:
            self._config.config["wifi_aps"] = wifi_aps
        else:
            self._config.config.pop("wifi_aps")
