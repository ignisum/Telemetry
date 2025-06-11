from enum import Enum
from PySide6.QtWidgets import *

class CustomColumn:
    def __init__(self, title: str, tool_tip: str):
        self.title = title
        self.tool_tip = tool_tip


class Columns(Enum):
    ID = CustomColumn("ID", "Уникальный идентификатор пакета")
    COUNTER = CustomColumn("Счётчик", "Счетчик пакетов")
    TIME = CustomColumn("Время", "Временная метка")
    VALUE = CustomColumn("Значение", "Полезная нагрузка пакета")
    CRC = CustomColumn("CRC16", "Контрольная сумма пакета")
    STATUS = CustomColumn("Статус", "Статус обработки пакета")
    SESSION = CustomColumn("Сеанс", "ID сеанса")


class PacketTable(QTableWidget):
    def __init__(self, parent):
        super().__init__(parent)

        self.setColumnCount(len(Columns))
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        for index, column in enumerate(Columns):
            custom_column: CustomColumn = column.value
            item = QTableWidgetItem(custom_column.title)
            item.setToolTip(custom_column.tool_tip)
            self.setHorizontalHeaderItem(index, item)
