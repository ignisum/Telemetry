import psycopg2
from typing import Optional, Dict, Any


class PostgresManager:
    def __init__(self, config: Dict[str, Any]):
        self.conn = psycopg2.connect(**config)
        self.conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        self.cursor = self.conn.cursor()

    def listen_channel(self, channel: str):
        self.cursor.execute(f"LISTEN {channel};")

    def get_notifications(self) -> Optional[Dict]:
        self.conn.poll()
        if self.conn.notifies:
            return self.conn.notifies.pop(0)
        return None

    def get_packet(self, packet_id: int) -> Optional[Dict]:
        self.cursor.execute(
            "SELECT id, packet_counter, timestamp, payload, crc16 FROM packets WHERE id = %s",
            (packet_id,)
        )
        if data := self.cursor.fetchone():
            return {
                "id": data[0],
                "counter": data[1],
                "timestamp": data[2],
                "payload": data[3],
                "crc16": data[4]
            }
        return None