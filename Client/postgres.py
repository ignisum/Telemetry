import logging
from typing import Dict, Any, List

import psycopg2

from row_models import Session, TelemetryPacket


class PostgresManager:
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        config["client_encoding"] = "utf-8"
        self.conn = psycopg2.connect(**config)
        self.conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        self.cursor = self.conn.cursor()

    def get_sessions(self) -> List[Session]:
        try:
            self.cursor.execute("""
                SELECT "Id", "Name", "StartTime", "EndTime"
                FROM public."Sessions"
                ORDER BY "StartTime" DESC
                """)
            sessions = []
            for row in self.cursor.fetchall():
                try:
                    sessions.append(Session(
                        id=row[0],
                        name=row[1],
                        start_time=row[2].timestamp() if row[2] else None,
                        end_time=row[3].timestamp() if row[3] else None
                    ))
                except Exception as e:
                    self.logger.error("Ошибка обработки сессии: %s", str(e))
            return sessions
        except Exception as e:
            self.logger.error("Ошибка БД в get_sessions: %s", str(e))
            return []

    def get_session_packets(self, session_id: int) -> List[TelemetryPacket]:
        if session_id is None:
            raise ValueError("Session ID не может быть None")

        try:
            self.cursor.execute("""
                SELECT "Packets"."Id", "PacketCounter", "Timestamp", "Payload", "Crc16", "SessionId" 
                FROM public."Packets"
                WHERE "SessionId" = %s 
                ORDER BY "Timestamp"
                """, (session_id,))
            packets = []
            for row in self.cursor.fetchall():
                try:
                    packets.append(TelemetryPacket(
                        id=row[0],
                        counter=row[1],
                        timestamp=row[2],
                        payload=row[3],
                        crc16=row[4],
                        session_id=row[5],
                        status='OK'
                    ))
                except Exception as e:
                    self.logger.error("Ошибка обработки пакета: %s", str(e))
            return packets
        except Exception as e:
            self.logger.error("Ошибка БД get_session_packets: %s", str(e))
            return []

    def close(self):
        try:
            if hasattr(self, 'cursor') and self.cursor:
                self.logger.info("Соединение с БД закрыто")
                self.cursor.close()
        except Exception as e:
            self.logger.error("Ошибка закрытия курсора: %s", str(e))

        try:
            if hasattr(self, 'conn') and self.conn:
                if not self.conn.closed:
                    self.conn.close()
        except Exception as e:
            self.logger.error("Ошибка закрытия соединения: %s", str(e))