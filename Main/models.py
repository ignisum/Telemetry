from dataclasses import dataclass
from datetime import datetime


@dataclass
class TelemetryPacket:
    id: int
    counter: int
    timestamp: float
    payload: float
    crc16: int
    status: str = "OK"

    @property
    def formatted_time(self):
        return datetime.fromtimestamp(self.timestamp).strftime('%Y-%m-%d %H:%M:%S')