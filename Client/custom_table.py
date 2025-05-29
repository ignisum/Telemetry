from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from models import TelemetryPacket
from constants import Columns, Tooltips


class PacketTable(QTableWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        self.setColumnCount(7)
        for index, column in enumerate(Columns):
            item = QTableWidgetItem(column.value)
            item.setToolTip(Tooltips[column.name].value)
            self.setHorizontalHeaderItem(index, item)

        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    # def add_packet(self, packet: TelemetryPacket):
    #     row = self.rowCount()
    #     self.insertRow(row)
    #
    #     bg_color = QColor(255, 200, 200) if packet.status == "NegativeValue" else QColor(240, 240, 240)
    #
    #     items = [
    #         QTableWidgetItem(str(packet.id)),
    #         QTableWidgetItem(str(packet.counter)),
    #         QTableWidgetItem(packet.formatted_time),
    #         QTableWidgetItem(f"{packet.payload:.4f}"),
    #         QTableWidgetItem(hex(packet.crc16)),
    #         QTableWidgetItem(packet.status),
    #         QTableWidgetItem(str(packet.session_id))
    #     ]
    #
    #     for col, item in enumerate(items):
    #         item.setBackground(QBrush(bg_color))
    #         item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
    #         self.setItem(row, col, item)
    #
    #     self.scrollToBottom()
