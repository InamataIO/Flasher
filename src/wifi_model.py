from PySide6 import QtCore
from PySide6.QtCore import QAbstractListModel, QModelIndex

from config import Config


class WiFiModel(QAbstractListModel):
    class AP:
        def __init__(self, ssid, password, checked=False):
            self.ssid: str = ssid
            self.password: str = password
            # If the AP is checked (selected) in the Qt list
            self.checked = checked

        def __str__(self) -> str:
            if self.password:
                return f"{self.ssid}:{'•'*len(self.password)}"
            return f"{self.ssid}"

    def __init__(self, config: Config, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._config = config
        ap_config = config.config.get("wifi_aps", [])
        self.aps: list[self.AP] = [
            self.AP(ssid=i["ssid"], password=i["password"]) for i in ap_config
        ]
        # If only one AP is present mark it checked by default
        if len(self.aps) == 1:
            self.aps[0].checked = True

    def data(self, index: QModelIndex, role) -> str:
        match role:
            case QtCore.Qt.DisplayRole:
                ap = self.aps[index.row()]
                return str(ap)
            case QtCore.Qt.CheckStateRole:
                ap = self.aps[index.row()]
                return QtCore.Qt.Checked if ap.checked else QtCore.Qt.Unchecked

    def toggle_checked(self, index: QModelIndex):
        ap = self.aps[index.row()]
        ap.checked = not ap.checked
        self.dataChanged.emit(index, index)

    def flags(self, index: QModelIndex) -> QtCore.Qt.ItemFlag:
        return QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsUserCheckable

    def rowCount(self, parent=QtCore.QModelIndex()) -> int:
        return len(self.aps)

    def ap_count(self) -> int:
        return len(self.aps)

    def add_ap(self, ssid, password, checked=False) -> None:
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        # Remove existing AP if it has the same SSID
        self.aps: list[self.AP] = [i for i in self.aps if i.ssid != ssid]
        self.aps.append(self.AP(ssid=ssid, password=password, checked=checked))
        self.endInsertRows()

    def remove_all_aps(self) -> None:
        indexes = (QModelIndex(), 0, len(self.aps) - 1)
        self.aps.clear()
        self._config.config.pop("wifi_aps", None)
        self.dataChanged.emit(*indexes)

    def get_ap(self, index: QModelIndex) -> AP:
        """Get the AP at the specified index."""
        return self.aps[index.row()]

    def get_checked_aps(self) -> list[AP]:
        """Get the list of checked APs."""
        return [ap for ap in self.aps if ap.checked]

    def remove_checked_aps(self) -> list[AP]:
        """Remove all checked APs."""
        indexes = (QModelIndex(), 0, len(self.aps) - 1)
        self.beginRemoveRows(*indexes)
        self.aps = [ap for ap in self.aps if not ap.checked]
        self.endRemoveRows()
        self.dataChanged.emit(*indexes)

    def save_to_config(self) -> None:
        """Save the current APs to the config"""
        wifi_aps = [{"ssid": i.ssid, "password": i.password} for i in self.aps]
        if wifi_aps:
            self._config.config["wifi_aps"] = wifi_aps
        else:
            self._config.config.pop("wifi_aps", None)
