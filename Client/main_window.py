import json
from datetime import datetime
from typing import Optional

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QMainWindow, QMessageBox, QTableWidgetItem, QHeaderView

from config import Config
from constants import Columns, Tooltips
from core import SignalRClient, TelemetryApiClient
from models import TelemetryPacket
from postgres import PostgresManager
from ui_telemetry_client import Ui_MainWindow


class MainWindow(QMainWindow):
    MAX_RECONNECT_ATTEMPTS = 5
    BASE_RECONNECT_INTERVAL = 15000

    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.current_packet_counter = 0
        self.signalr_connected = False
        self.is_generation_active = False
        self.current_reconnect_attempt = 0

        self.signalr = SignalRClient(f'{Config.SERVER_URL}/telemetryhub')
        self.api = TelemetryApiClient(Config.SERVER_URL + "/api/Telemetry")
        self.db = PostgresManager(Config.DB_CONFIG)

        self.db_connected = False
        self.check_db_connection()

        self.init_ui()
        self.setup_connections()
        self.setup_timers()
        self.update_ui_state()

    def init_ui(self):
        self.setWindowTitle("Телеметрический клиент")

        for table in [self.ui.PacketTableWidget, self.ui.tableSessionPackets]:
            table.setColumnCount(len(Columns))
            table.setHorizontalHeaderLabels([col.value for col in Columns])

            header = table.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.Stretch)
            header.setDefaultAlignment(Qt.AlignCenter)

            for i, col in enumerate(Columns):
                table.horizontalHeaderItem(i).setToolTip(Tooltips[col.name].value)

    def setup_connections(self):
        self.ui.btnConnect.clicked.connect(self.toggle_connection)
        self.ui.btnStart.clicked.connect(self.start_generation)
        self.ui.btnStop.clicked.connect(self.stop_generation)
        self.ui.btnRefreshSessions.clicked.connect(self.refresh_sessions)

        self.signalr.on_packet_received(self.handle_new_packet)
        self.signalr.connection.on_open(self.on_connected)
        self.signalr.connection.on_close(self.on_disconnected)
        self.signalr.connection.on_error(self.on_error)

        self.ui.listSessions.itemSelectionChanged.connect(self.load_session_packets)

    def setup_timers(self):
        self.db_check_timer = QTimer()
        self.db_check_timer.timeout.connect(self.check_db_notifications)
        self.db_check_timer.start(1000)

    def check_db_connection(self):
        try:
            self.db.cursor.execute("SELECT 1")
            self.db_connected = True
        except Exception:
            self.db_connected = False
            self.show_error("Нет подключения к базе данных. Режим истории недоступен.")

    def refresh_sessions(self):
        try:
            sessions = self.db.get_sessions()
            self.ui.listSessions.clear()

            for session in sessions:
                start_str = session.formatted_start_time
                end_str = session.formatted_end_time if session.end_time else "Активна"

                self.ui.listSessions.addItem(
                    f"{session.id}: {session.name} ({start_str} - {end_str})"
                )

        except Exception as e:
            self.show_error(f"Ошибка загрузки сессий: {str(e)}")

    def load_session_packets(self):
        selected = self.ui.listSessions.currentItem()
        if not selected:
            return

        try:
            self.ui.tableSessionPackets.setRowCount(0)
            session_text = selected.text()

            try:
                session_id_str, *rest = session_text.split(":", 1)
                session_id = int(session_id_str.strip())
            except (ValueError, IndexError) as e:
                raise ValueError(f"Неверный формат ID сессии: {session_text}") from e

            try:
                if not rest:
                    raise ValueError("Отсутствует название сессии")

                session_info = rest[0].strip()
                if "(" not in session_info or ")" not in session_info:
                    session_name = session_info
                    time_range = "N/A"
                else:
                    session_name, time_part = session_info.split("(", 1)
                    session_name = session_name.strip()
                    time_range = time_part.split(")")[0].strip()
            except Exception as e:
                print(f"Ошибка парсинга названия сессии: {str(e)}")
                session_name = "Неизвестная сессия"
                time_range = "N/A"

            packets = self.db.get_session_packets(session_id)
            packet_count = len(packets) if packets else 0

            self.ui.lblSessionInfo.setText(
                f"Сессия: {session_name} | Диапазон: {time_range} | Пакетов: {packet_count}"
            )

            if not packets:
                self.show_error("Для выбранной сессии нет пакетов данных")
                return

            for packet in packets:
                if not hasattr(packet, '__dict__'):
                    print(f"Некорректный объект пакета: {packet}")
                    continue

                self.add_packet_to_table(
                    self.ui.tableSessionPackets,
                    packet.__dict__,
                    f"{session_id}: {session_name}"
                )

        except ValueError as ve:
            self.show_error(f"Ошибка формата данных: {str(ve)}")
        except Exception as e:
            self.show_error(f"Ошибка загрузки пакетов: {str(e)}")
            print(f"Подробности ошибки: {repr(e)}")

    def handle_new_packet(self, packet):
        try:
            parsed = self.parse_packet(packet)
            if parsed:
                self.current_packet_counter += 1
                session_text = f"Сессия {self.current_session_id}" if hasattr(self, 'current_session_id') else None
                self.add_packet_to_table(self.ui.PacketTableWidget, parsed.__dict__, session_text)
        except Exception as e:
            print(f"Ошибка обработки пакета: {str(e)}")

    def add_packet_to_table(self, table, packet, session_info=None):
        row = table.rowCount()
        table.insertRow(row)

        payload = packet.get('payload', 0)
        counter = packet.get('counter', packet.get('packetCounter', 'N/A'))
        time_str = self.format_time(packet.get('timestamp'))

        items = [
            str(packet.get('id', 'N/A')),
            str(counter),
            time_str,
            f"{payload:.4f}",
            hex(packet.get('crc16', 0)),
            'NegativeValue' if payload < 0 else 'OK',
            str(session_info) if session_info else "Текущая"
        ]

        for col, text in enumerate(items):
            item = QTableWidgetItem(text)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if payload < 0:
                item.setBackground(QColor(255, 230, 230))
            table.setItem(row, col, item)

    def parse_packet(self, raw_packet) -> Optional[TelemetryPacket]:
        if isinstance(raw_packet, str):
            try:
                raw_packet = json.loads(raw_packet)
            except json.JSONDecodeError:
                return None

        if isinstance(raw_packet, list) and raw_packet:
            raw_packet = raw_packet[0]

        if not isinstance(raw_packet, dict):
            return None

        try:
            return TelemetryPacket(
                id=raw_packet.get('id', 0),
                counter=raw_packet.get('packetCounter', 0),
                timestamp=raw_packet.get('timestamp'),
                payload=raw_packet.get('payload', 0.0),
                crc16=raw_packet.get('crc16', 0),
                status='NegativeValue' if raw_packet.get('payload', 0) < 0 else 'OK'
            )
        except Exception:
            return None

    def format_time(self, time_value):
        if not time_value:
            return "N/A"
        try:
            if isinstance(time_value, (int, float)):
                return datetime.fromtimestamp(time_value).strftime('%Y-%m-%d %H:%M:%S')
            elif 'T' in str(time_value):
                return datetime.fromisoformat(str(time_value).replace('T', ' ')).strftime('%Y-%m-%d %H:%M:%S')
            else:
                return datetime.strptime(str(time_value), '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            return "N/A"

    def start_generation(self):
        if not self.signalr_connected:
            self.show_error("Сначала подключитесь к серверу")
            return

        try:
            self.current_packet_counter = 0
            self.ui.PacketTableWidget.setRowCount(0)

            session_name = f"Сессия {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            session_data = self.api.start_session(session_name).json()
            self.current_session_id = session_data['SessionId']

            if self.api.start_generation(self.current_session_id).status_code == 200:
                self.is_generation_active = True
                self.update_ui_state()
        except Exception as e:
            self.show_error(f"Ошибка запуска: {str(e)}")
            self.is_generation_active = False
            self.update_ui_state()

    def stop_generation(self):
        try:
            if self.api.stop_generation().status_code == 200:
                self.is_generation_active = False
                self.update_ui_state()
        except Exception as e:
            self.show_error(f"Ошибка остановки: {e}")

    def toggle_connection(self):
        try:
            if self.signalr_connected:
                self.signalr.disconnect()
            else:
                self.signalr.connect()
        except Exception as e:
            print(f"Ошибка переключения подключения: {str(e)}")

    def check_db_notifications(self):
        if notification := self.db.get_notifications():
            if packet := self.db.get_packet(int(notification.payload)):
                self.handle_new_packet(packet)

    def check_server_status(self):
        if not self.signalr_connected and self.current_reconnect_attempt < self.MAX_RECONNECT_ATTEMPTS:
            self.current_reconnect_attempt += 1
            self.signalr.connect()

            try:
                http_ok = self.api.get_status().status_code == 200
                status = f"HTTP: {'OK' if http_ok else 'ERROR'} | SignalR: {'CONNECTED' if self.signalr_connected else 'DISCONNECTED'}"
                self.ui.statusbar.showMessage(status)
            except Exception:
                self.ui.statusbar.showMessage("Сервер недоступен", 3000)

    def on_connected(self):
        self.signalr_connected = True
        self.current_reconnect_attempt = 0
        self.update_ui_state()

    def on_disconnected(self):
        self.signalr_connected = False
        self.is_generation_active = False
        self.update_ui_state()
        self.ui.statusbar.showMessage("SignalR отключен")

    def on_error(self, error: str):
        self.ui.statusbar.showMessage(f"SignalR error: {error}")

    def update_ui_state(self):
        self.ui.btnConnect.setText("Отключиться" if self.signalr_connected else "Подключиться")
        self.ui.btnStart.setEnabled(self.signalr_connected and not self.is_generation_active)
        self.ui.btnStop.setEnabled(self.is_generation_active)
        self.ui.statusbar.showMessage(f"Генерация: {'ВКЛ' if self.is_generation_active else 'ВЫКЛ'}")
        db_status = "БД: ✔" if self.db_connected else "БД: ✖"
        self.ui.statusbar.showMessage(
            f"{db_status} | Генерация: {'ВКЛ' if self.is_generation_active else 'ВЫКЛ'}"
        )

    def show_error(self, message):
        QMessageBox.critical(self, "Ошибка", message)
        self.ui.statusbar.showMessage(f"Ошибка: {message}", 5000)

    def closeEvent(self, event):
        self.signalr.disconnect()
        self.db.conn.close()
        self.db_check_timer.stop()
        event.accept()
