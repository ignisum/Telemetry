from dataclasses import dataclass
from datetime import datetime
from constants import Columns
from typing import List, Optional


@dataclass
class TelemetryPacket:
    id: int
    counter: int
    timestamp: float
    payload: float
    crc16: int
    session_id: Optional[int] = None
    status: str = "OK"

    @property
    def formatted_time(self):
        return datetime.fromtimestamp(self.timestamp).strftime('%Y-%m-%d %H:%M:%S')

    @classmethod
    def get_column_names(cls):
        return ([col.value for col in Columns])

@dataclass
class Session:
    id: int
    name: str
    start_time: float
    end_time: Optional[float] = None
    session_id: Optional[int] = None

    @property
    def formatted_start_time(self):
        return datetime.fromtimestamp(self.start_time).strftime('%Y-%m-%d %H:%M:%S')

    @property
    def formatted_end_time(self):
        if self.end_time:
            return datetime.fromtimestamp(self.end_time).strftime('%Y-%m-%d %H:%M:%S')
        return "В процессе"
