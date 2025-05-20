import psycopg2
from typing import Optional, Dict, Any, List
from models import Session, TelemetryPacket


class PostgresManager:
    def __init__(self, config: Dict[str, Any]):
        config["client_encoding"] = "utf-8"
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

    def get_packet(self, packet_id: int) -> Optional[TelemetryPacket]:
        self.cursor.execute(
            "SELECT id, packet_counter, timestamp, payload, crc16, session_id FROM Packets WHERE id = %s",
            (packet_id,)
        )
        if data := self.cursor.fetchone():
            return TelemetryPacket(
                id=data[0],
                counter=data[1],
                timestamp=data[2],
                payload=data[3],
                crc16=data[4],
                session_id=data[5]
            )
        return None
    def create_session(self, name: str) -> Session:
        self.cursor.execute(
           """ "INSERT INTO "Sessions" (name) VALUES (%s) RETURNING id, startTime",
            name """
        )
        session_id, start_time = self.cursor.fetchone()
        self.conn.commit()
        return Session(id=session_id, name=name, start_time=start_time.timestamp())

    def get_sessions(self) -> List[Session]:
        try:
            self.cursor.execute("""
                SELECT "Id", "Name", "StartTime", "EndTime"
                FROM "Sessions"
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
                    print(f"Ошибка обработки сессии: {str(e)}")
            return sessions
        except Exception as e:
            print(f"Ошибка БД в get_sessions: {str(e)}")
            return []

    def get_session_packets(self, session_id: int) -> List[TelemetryPacket]:
        if session_id is None:
            raise ValueError("Session ID не может быть None")

        try:
            self.cursor.execute("""
                SELECT "Packets"."Id", "PacketCounter", "Timestamp", "Payload", "Crc16", "SessionId" 
                FROM "Packets"
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
                    print(f"Ошибка обработки пакета: {str(e)}")
            return packets
        except Exception as e:
            print(f"Ошибка БД get_session_packets: {str(e)}")
            return []
