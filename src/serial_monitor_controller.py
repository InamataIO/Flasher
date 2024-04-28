import logging

import serial
from PySide6.QtCore import QCoreApplication, QObject, QThread, Signal, Slot
from PySide6.QtWidgets import QScrollBar
from serial.serialutil import SerialException

from config import Config
from serial_monitor_view import SerialMonitorView


class WorkerSignals(QObject):
    alive = Signal(bool)
    read_data = Signal(bytes)
    error = Signal(Exception)
    finished = Signal()


class SerialThread(QThread):
    def __init__(self, port: str):
        super().__init__()
        self.signals = WorkerSignals()
        self.alive = True
        self.signals.alive.connect(self.update_alive)
        self.serial = serial.Serial(
            port=port, baudrate=115200, xonxoff=False, rtscts=False, dsrdtr=False
        )
        self.serial.timeout = 0.25

    def update_alive(self, state) -> None:
        self.alive = state

    @Slot()
    def run(self):
        try:
            self.read_serial()
        except SerialException as error:
            logging.warning(error)
            self.signals.error.emit(error)
        except Exception as error:
            logging.exception(error)
            self.signals.error.emit(error)
        finally:
            self.serial.close()
            self.signals.finished.emit()

    def read_serial(self):
        while self.alive:
            data = self.serial.read(self.serial.in_waiting or 1)
            if data:
                # TODO: buffer data here by line and timeout
                self.signals.read_data.emit(data.decode())


class SerialMonitorController:
    def __init__(self, view: SerialMonitorView, config: Config) -> None:
        self._config = config
        self._view = view
        self.thread: QThread | None = None
        self.ports: serial.tools.list_ports.ListPortInfo = []
        self._connect_signals()
        self._update_com_ports()

    def _connect_signals(self):
        self._view.ui.startStopButton.clicked.connect(self.start_stop_monitor)
        self._view.ui.updateComButton.clicked.connect(self._update_com_ports)
        self._view.ui.closeButton.clicked.connect(self._view.close)

    def _update_com_ports(self):
        self.ports = serial.tools.list_ports.comports()
        self._view.ui.comPortsComboBox.clear()
        current_port = self._view.ui.comPortsComboBox.currentData()
        for i in self.ports:
            self._view.ui.comPortsComboBox.addItem(i[0], userData=i)
        if current_port:
            index = self._view.ui.comPortsComboBox.findData(current_port)
            if index:
                self._view.ui.comPortsComboBox.setCurrentIndex(index)
        if not self._view.ui.comPortsComboBox.count():
            self._stop_monitor()
            self._view.ui.comPortsComboBox.addItem(self.no_com_ports_label, None)

    def start_stop_monitor(self) -> None:
        if not self.ports:
            self._view.notify(self.no_com_ports_message, self.no_com_ports_label)
            self._stop_monitor()
            return
        if self.thread:
            self._stop_monitor()
        else:
            self._start_monitor()

    def _stop_monitor(self):
        if not self.thread:
            return
        self.stop_thread()
        self._view.set_start_stop_icon(False)

    def _start_monitor(self):
        if self.thread:
            return
        self._view.ui.monitorTextEdit.clear()
        self._view.set_start_stop_icon(True)
        self.start_thread()

    def start_thread(self):
        """Start the receiver thread"""
        if self.thread is not None:
            return
        current_port = self._view.ui.comPortsComboBox.currentData()
        if not current_port:
            return
        self.thread = SerialThread(current_port[0])
        self.thread.signals.read_data.connect(self.read_data)
        self.thread.signals.error.connect(self.thread_error)
        self.thread.signals.finished.connect(self.thread_finished)
        self.thread.start()

    def stop_thread(self):
        """Stop the receiver thread, wait until it's finished."""
        if self.thread is None:
            return
        self.thread.signals.alive.emit(False)
        self.thread.wait()
        self.thread = None

    def close(self):
        self.stop_thread()

    def read_data(self, data: str) -> None:
        """Write read data to text edit and scroll to bottom if already there."""
        scrollbar: QScrollBar = self._view.ui.monitorTextEdit.verticalScrollBar()
        at_bottom = scrollbar.value() == scrollbar.maximum()
        self._view.ui.monitorTextEdit.insertPlainText(data)
        if at_bottom:
            scrollbar.setValue(scrollbar.maximum())

    def thread_error(self, error: Exception) -> None:
        if isinstance(error, SerialException):
            self._view.notify(
                str(error), self.serial_port_disconnected_title, level="warning"
            )
        else:
            self._view.notify(str(error), self.serial_port_error_title, level="error")
        self._update_com_ports()

    def thread_finished(self) -> None:
        self._view.set_start_stop_icon(False)

    @property
    def no_com_ports_label(self) -> str:
        return QCoreApplication.translate("serial", "No COM ports found")

    @property
    def no_com_ports_message(self) -> str:
        return QCoreApplication.translate(
            "serial",
            """No connected serial devices were found. Check if

1. the device is connected
2. the USB cable is too long
3. another port on your computer works
4. unplugging it and plugging it in again helps""",
        )

    @property
    def serial_port_disconnected_title(self) -> str:
        return QCoreApplication.translate("serial", "Serial port disconnected")

    @property
    def serial_port_error_title(self) -> str:
        return QCoreApplication.translate("serial", "Unknown connection error")
