from typing import List

from PySide2 import QtCore
from PySide2.QtCore import QAbstractListModel, QModelIndex

from config import DSFlasherConfig


class DSFlasherWiFiModel(QAbstractListModel):
    class AP:
        def __init__(self, ssid, password):
            self.ssid: str = ssid
            self.password: str = password

        def __str__(self):
            return f"{self.ssid}:{self.password}"

    def __init__(self, config: DSFlasherConfig, aps: List[AP] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._config = config
        self.aps: List[self.AP] = aps or []
        ap_config = config.config.get("wifi_aps", [])
        new_aps = [self.AP(ssid=i["ssid"], password=i["password"]) for i in ap_config]
        self.aps.extend(new_aps)

    def data(self, index, role) -> str:
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

    def save_to_config(self):
        """Save the current APs to the config file"""
        self._config.config["wifi_aps"] = [
            {"ssid": i.ssid, "password": i.password} for i in self.aps
        ]
