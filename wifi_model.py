from typing import List
from PySide2 import QtCore
from PySide2.QtCore import QAbstractListModel, QModelIndex

class DSFlasherWiFiModel(QAbstractListModel):
    class AP:
        def __init__(self, ssid, password):
            self.ssid: str = ssid
            self.password: str = password

        def __str__(self):
            return f"{self.ssid}:{self.password}"

    def __init__(self, *args, aps: List[AP]=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.aps: List[self.AP] = aps or []
    
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
        self.aps.append(self.AP(ssid=ssid, password=password))
        self.endInsertRows()
    
    def remove_ap(self, row):
        self.beginRemoveRows(QModelIndex(), row, row)
        self.aps.pop(row)
        self.endRemoveRows()
