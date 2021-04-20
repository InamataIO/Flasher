from typing import List
from PySide2 import QtCore

class DSFlasherWiFiModel(QtCore.QAbstractListModel):
    class AP:
        ssid: str = ""
        password: str = ""

        def __str__(self):
            return f"{self.ssid}:{self.password}"

    def __init__(self, *args, aps: List[AP]=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.aps = aps or []
    
    def data(self, index, role) -> str:
        if role == QtCore.Qt.DisplayRole:
            _, ap = self.aps[index.row()]
            return str(ap)
    
    def rowCount(self, index):
        return len(self.aps)
    
    def ap_count(self):
        return len(self.aps)