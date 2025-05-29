from enum import Enum


class Columns(Enum):
    ID = "ID"
    COUNTER = "Счётчик"
    TIME = "Время"
    VALUE = "Значение"
    CRC = "CRC16"
    STATUS = "Статус"
    SESSION = "Сеанс"


class Tooltips(Enum):
    ID = "Уникальный идентификатор пакета"
    COUNTER = "Счетчик пакетов"
    TIME = "Временная метка"
    VALUE = "Полезная нагрузка пакета"
    CRC = "Контрольная сумма пакета"
    STATUS = "Статус обработки пакета"
    SESSION = "ID сеанса"
