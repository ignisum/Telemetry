from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from models import TelemetryPacket


class PacketTable(QTableWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        self.setColumnCount(6)
        self.setHorizontalHeaderLabels([
            "ID", "Счётчик", "Время", "Значение", "CRC16", "Статус"
        ])

        self.model().setHeaderData(0, Qt.Horizontal, "Уникальный идентификатор пакета", Qt.ToolTipRole)
        self.model().setHeaderData(1, Qt.Horizontal, "Счетчик пакетов", Qt.ToolTipRole)
        self.model().setHeaderData(2, Qt.Horizontal, "Временная метка", Qt.ToolTipRole)
        self.model().setHeaderData(3, Qt.Horizontal, "Полезная нагрузка пакета", Qt.ToolTipRole)
        self.model().setHeaderData(4, Qt.Horizontal, "Контрольная сумма пакета", Qt.ToolTipRole)
        self.model().setHeaderData(5, Qt.Horizontal, "Статус обработки пакета", Qt.ToolTipRole)

        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def add_packet(self, packet: TelemetryPacket):
        row = self.rowCount()
        self.insertRow(row)

        bg_color = QColor(255, 200, 200) if packet.status == "NegativeValue" else QColor(240, 240, 240)

        items = [
            QTableWidgetItem(str(packet.id)),
            QTableWidgetItem(str(packet.counter)),
            QTableWidgetItem(packet.formatted_time),
            QTableWidgetItem(f"{packet.payload:.4f}"),
            QTableWidgetItem(hex(packet.crc16)),
            QTableWidgetItem(packet.status)
        ]

        for col, item in enumerate(items):
            item.setBackground(QBrush(bg_color))
            item.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, col, item)

        self.scrollToBottom()