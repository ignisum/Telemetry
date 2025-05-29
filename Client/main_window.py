import json
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional, Dict, Any, List, Tuple, Union
import logging

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QMainWindow, QMessageBox, QTableWidgetItem, QHeaderView

from config import Config
from constants import Columns, Tooltips
from core import SignalRClient, TelemetryApiClient
from models import TelemetryPacket, Session
from postgres import PostgresManager
from ui_telemetry_client import Ui_MainWindow


class MainWindow(QMainWindow):
    MAX_RECONNECT_ATTEMPTS: int = 5
    BASE_RECONNECT_INTERVAL: int = 15000

    def __init__(self) -> None:
        super().__init__()
        self._setup_logging()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.current_packet_counter: int = 0
        self.signalr_connected: bool = False
        self.is_generation_active: bool = False
        self.current_reconnect_attempt: int = 0

        self.signalr: SignalRClient = SignalRClient(f'{Config.SERVER_URL}/telemetryhub')
        self.api: TelemetryApiClient = TelemetryApiClient(Config.SERVER_URL + "/api/Telemetry")
        self.db: PostgresManager = PostgresManager(Config.DB_CONFIG)

        self.db_connected: bool = False
        self.check_db_connection()



        self.init_ui()
        self.setup_connections()
        self.setup_timers()
        self.update_ui_state()

    def _setup_logging(self) -> None:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                RotatingFileHandler(
                    'telemetry_client.log',
                    encoding='utf-8'
                ),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def init_ui(self) -> None:
        self.setWindowTitle("Телеметрический клиент")

        for table in [self.ui.PacketTableWidget, self.ui.tableSessionPackets]:
            table.setColumnCount(len(Columns))
            table.setHorizontalHeaderLabels([col.value for col in Columns])

            header = table.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.Stretch)
            header.setDefaultAlignment(Qt.AlignCenter)

            for i, col in enumerate(Columns):
                table.horizontalHeaderItem(i).setToolTip(Tooltips[col.name].value)

    def setup_connections(self) -> None:
        self.ui.btnConnect.clicked.connect(self.toggle_connection)
        self.ui.btnStart.clicked.connect(self.start_generation)
        self.ui.btnStop.clicked.connect(self.stop_generation)
        self.ui.btnRefreshSessions.clicked.connect(self.refresh_sessions)

        self.signalr.on_packet_received(self.handle_new_packet)
        self.signalr.connection.on_open(self.on_connected)
        self.signalr.connection.on_close(self.on_disconnected)
        self.signalr.connection.on_error(self.handle_error)

        self.ui.listSessions.itemSelectionChanged.connect(self.load_session_packets)

    def setup_timers(self) -> None:
        self.db_check_timer = QTimer()
        self.db_check_timer.timeout.connect(self.check_db_notifications)
        self.db_check_timer.start(1000)

    def check_db_connection(self) -> None:
        if not hasattr(self, 'db') or not hasattr(self.db, 'cursor'):
            self.db_connected = False
            self.logger.error("Ошибка подключения к БД: отсутствует атрибут db или cursor")
            QMessageBox.critical(
                self,
                "Ошибка БД",
                "Не удалось подключиться к базе данных!",
                QMessageBox.StandardButton.Ok
            )
            return

        self.db_connected = self.db.cursor is not None
        if not self.db_connected:
            self.logger.error("Курсор БД не инициализирован")
            QMessageBox.critical(
                self,
                "Ошибка БД",
                "Курсор БД не инициализирован!",
                QMessageBox.StandardButton.Ok
            )
        else:
            self.logger.info("Подключение к БД установлено")

    def refresh_sessions(self) -> None:
        if not self.db_connected or not hasattr(self.db, 'get_sessions'):
            self.logger.warning("Попытка обновить сессии без подключения к БД")
            self.show_error("Нет подключения к БД")
            return

        sessions = self.db.get_sessions()
        if not sessions:
            self.ui.listSessions.clear()
            self.logger.debug("В базе данных не найдено сессий")
            return

        self.ui.listSessions.clear()
        for session in sessions:
            if not hasattr(session, 'formatted_start_time') or not hasattr(session, 'formatted_end_time'):
                self.logger.warning(f"Некорректный объект сессии: {session}")
                continue

            start_str = session.formatted_start_time
            end_str = session.formatted_end_time if session.end_time else "Активна"
            self.ui.listSessions.addItem(f"{session.id}: {session.name} ({start_str} - {end_str})")

        self.logger.info(f"Список сессий обновлен, количество: {len(sessions)}")

    def load_session_packets(self) -> None:
        selected = self.ui.listSessions.currentItem()
        if not selected:
            return

        session_text = selected.text()
        parts = session_text.split(":", 1)

        if len(parts) < 2:
            self.logger.warning(f"Неверный формат сессии: {session_text}")
            self.show_error("Неверный формат записи сессии")
            return

        session_id_str, rest = parts[0].strip(), parts[1].strip()
        if not session_id_str.isdigit():
            self.logger.warning(f"Неверный формат ID сессии: {session_id_str}")
            self.show_error(f"Неверный формат ID сессии: {session_id_str}")
            return

        session_id = int(session_id_str)
        self.logger.debug(f"Загрузка пакетов для сессии ID: {session_id}")

        session_name = "Неизвестная сессия"
        time_range = "N/A"

        if "(" in rest and ")" in rest:
            name_part, time_part = rest.split("(", 1)
            session_name = name_part.strip()
            time_range = time_part.split(")")[0].strip()
        else:
            session_name = rest.strip()

        packets = self.db.get_session_packets(session_id)
        if not packets:
            self.logger.info(f"Для сессии {session_id} не найдено пакетов")
            self.show_error("Для выбранной сессии нет пакетов данных")
            return

        self.ui.tableSessionPackets.setRowCount(0)
        packet_count = len(packets)
        self.ui.lblSessionInfo.setText(
            f"Сессия: {session_name} | Диапазон: {time_range} | Пакетов: {packet_count}"
        )

        for packet in packets:
            packet_data = {
                'id': packet.id,
                'counter': packet.counter,
                'timestamp': packet.timestamp,
                'payload': packet.payload,
                'crc16': packet.crc16,
                'status': packet.status
            }

            self.add_packet_to_table(
                self.ui.tableSessionPackets,
                packet_data,
                f"{session_id}: {session_name}"
            )

        self.logger.info(f"Загружено {packet_count} пакетов для сессии {session_id}")

    def handle_new_packet(self, packet: Union[dict, str, list]) -> None:
        if not packet:
            self.logger.debug("Получен пустой пакет")
            return

        parsed = self.parse_packet(packet)
        if not parsed:
            self.logger.warning("Не удалось распарсить пакет")
            return

        self.current_packet_counter += 1
        session_text = f"Сессия {self.current_session_id}" if hasattr(self, 'current_session_id') else None

        packet_data = {
            'id': parsed.id,
            'counter': parsed.counter,
            'timestamp': parsed.timestamp,
            'payload': parsed.payload,
            'crc16': parsed.crc16,
            'status': parsed.status
        }

        self.add_packet_to_table(self.ui.PacketTableWidget, packet_data, session_text)
        self.logger.debug(f"Обработан пакет #{self.current_packet_counter}")

    def prepare_packet_items(self, packet: dict, session_info: Optional[str] = None) -> List[str]:
        payload = packet.get('payload', 0)
        return [
            str(packet.get('id', 'N/A')),
            str(packet.get('counter', packet.get('packetCounter', 'N/A'))),
            self.format_time(packet.get('timestamp')),
            f"{payload:.4f}",
            hex(packet.get('crc16', 0)),
            'NegativeValue' if payload < 0 else 'OK',
            str(session_info) if session_info else "Текущая"
        ]

    def add_packet_to_table(self, table, packet: dict, session_info: Optional[str] = None) -> None:
        row = table.rowCount()
        table.insertRow(row)

        items = self.prepare_packet_items(packet, session_info)
        payload = packet.get('payload', 0)

        for col, text in enumerate(items):
            item = QTableWidgetItem(text)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if payload < 0:
                item.setBackground(QColor(255, 230, 230))
            table.setItem(row, col, item)

    def parse_packet(self, raw_packet: Union[dict, str, list]) -> Optional[TelemetryPacket]:
        if not raw_packet:
            return None

        if isinstance(raw_packet, str):
            try:
                raw_packet = json.loads(raw_packet)
            except json.JSONDecodeError as e:
                self.logger.error(f"Ошибка декодирования JSON: {e}")
                return None

        if isinstance(raw_packet, list):
            if raw_packet:
                raw_packet = raw_packet[0]
            else:
                return None

        if not isinstance(raw_packet, dict):
            return None

        payload = raw_packet.get('payload', 0)
        return TelemetryPacket(
            id=raw_packet.get('id', 0),
            counter=raw_packet.get('packetCounter', 0),
            timestamp=raw_packet.get('timestamp'),
            payload=payload,
            crc16=raw_packet.get('crc16', 0),
            status='NegativeValue' if payload < 0 else 'OK'
        )

    def format_time(self, time_value: Union[int, float, str, None]) -> str:
        if not time_value:
            return "N/A"

        try:
            if isinstance(time_value, (int, float)):
                return datetime.fromtimestamp(time_value).strftime('%Y-%m-%d %H:%M:%S')
            elif 'T' in str(time_value):
                return datetime.fromisoformat(str(time_value).replace('T', ' ')).strftime('%Y-%m-%d %H:%M:%S')
            else:
                return datetime.strptime(str(time_value), '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            self.logger.error(f"Ошибка формата времени: {e}")
            return "N/A"

    def start_generation(self) -> None:
        if not self.db_connected:
            self.logger.warning("Попытка запустить генерацию без подключения к БД")
            self.show_error("Нет подключения к БД! Данные не будут сохранены.")
            return

        if not self.signalr_connected:
            self.logger.warning("Попытка запустить генерацию без подключения к серверу")
            self.show_error("Сначала подключитесь к серверу")
            return

        self.current_packet_counter = 0
        self.ui.PacketTableWidget.setRowCount(0)

        session_name = f"Сессия {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        response = self.api.start_session(session_name)

        if response.status_code != 200:
            self.logger.error(f"Ошибка запуска сессии, код статуса: {response.status_code}")
            self.show_error("Ошибка создания сессии")
            return

        session_data = response.json()
        if 'SessionId' not in session_data:
            self.logger.error("Некорректный формат ответа сервера")
            self.show_error("Неверный формат ответа сервера")
            return

        self.current_session_id = session_data['SessionId']
        response = self.api.start_generation(self.current_session_id)

        if response.status_code == 200:
            self.is_generation_active = True
            self.update_ui_state()
            self.logger.info(f"Генерация запущена для сессии {self.current_session_id}")
        else:
            self.logger.error(f"Ошибка запуска генерации, код статуса: {response.status_code}")
            self.show_error("Ошибка запуска генерации")

    def stop_generation(self) -> None:
        if not self.is_generation_active:
            return

        response = self.api.stop_generation()
        if response.status_code == 200:
            self.is_generation_active = False
            self.update_ui_state()
            self.logger.info("Генерация остановлена")
        else:
            self.logger.error(f"Ошибка остановки генерации, код статуса: {response.status_code}")
            self.show_error("Сервер не подтвердил остановку генерации")

    def toggle_connection(self) -> None:
        try:
            if self.signalr_connected:
                self.signalr.disconnect()
                self.logger.info("Отключено от сервера")
            else:
                self.signalr.connect()
                self.logger.info("Попытка подключения к серверу")
        except Exception as e:
            self.logger.error(f"Ошибка подключения: {e}")
            QMessageBox.critical(
                self,
                "Ошибка подключения",
                "Не удалось подключиться к серверу!",
                QMessageBox.StandardButton.Ok
            )

    def check_db_notifications(self) -> None:
        if notification := self.db.get_notifications():
            if packet := self.db.get_packet(int(notification.payload)):
                self.handle_new_packet(packet)
                self.logger.debug(f"Получено уведомление от БД для пакета {notification.payload}")

    def check_server_status(self) -> None:
        if not self.signalr_connected and self.current_reconnect_attempt < self.MAX_RECONNECT_ATTEMPTS:
            self.current_reconnect_attempt += 1
            self.signalr.connect()
            self.logger.info(f"Попытка переподключения #{self.current_reconnect_attempt}")

            try:
                http_ok = self.api.get_status().status_code == 200
                status = f"HTTP: {'OK' if http_ok else 'ERROR'} | SignalR: {'CONNECTED' if self.signalr_connected else 'DISCONNECTED'}"
                self.ui.statusbar.showMessage(status)
            except Exception as e:
                self.logger.error(f"Ошибка проверки статуса сервера: {e}")
                self.ui.statusbar.showMessage("Сервер недоступен", 3000)

    def on_connected(self) -> None:
        self.signalr_connected = True
        self.current_reconnect_attempt = 0
        self.update_ui_state()
        self.logger.info("Успешное подключение к серверу")

    def on_disconnected(self) -> None:
        self.signalr_connected = False
        self.is_generation_active = False
        self.update_ui_state()
        self.logger.info("Отключено от сервера")
        if "✔" in self.ui.statusbar.currentMessage():
            self.show_error("Соединение с сервером закрыто")

    def handle_error(self, error: str) -> None:
        error_msg = str(error)
        if not error_msg or "WinError" in error_msg:
            error_msg = "Сервер разорвал соединение"

        self.signalr_connected = False
        self.is_generation_active = False
        self.logger.error(f"Ошибка соединения: {error_msg}")

        QMessageBox.critical(
            self,
            "Ошибка соединения",
            f"Не удалось подключиться к серверу:\n\n{error_msg}",
            QMessageBox.StandardButton.Ok
        )

        self.update_ui_state()

    def update_ui_state(self) -> None:
        self.ui.btnConnect.setText("Отключиться" if self.signalr_connected else "Подключиться")
        self.ui.btnStart.setEnabled(self.signalr_connected and not self.is_generation_active)
        self.ui.btnStop.setEnabled(self.is_generation_active)
        self.check_db_connection()
        db_status = "БД: ✔" if self.db_connected else "БД: ✖"
        gen_status = f"Генерация: {'ВКЛ' if self.is_generation_active else 'ВЫКЛ'}"
        server_status = "Сервер: ОТКЛЮЧЕН" if not self.signalr_connected else "Сервер: ✔"

        self.ui.statusbar.showMessage(f"{db_status} | {gen_status} | {server_status}")

    def show_error(self, message: str) -> None:
        if not message.strip():
            message = "Произошла неизвестная ошибка"
        self.ui.statusbar.showMessage(f"ОШИБКА: {message}", 10000)
        if "разорвал" in message or "отключ" in message.lower():
            self.logger.error(f"Критическая ошибка: {message}")
            QMessageBox.critical(
                self,
                "Ошибка",
                message,
                QMessageBox.StandardButton.Ok
            )
        else:
            self.logger.warning(f"Предупреждение: {message}")

    def closeEvent(self, event) -> None:
        if self.is_generation_active:
            response = self.api.stop_generation()
            if response.status_code == 200:
                self.is_generation_active = False
                self.update_ui_state()
                self.logger.info("Генерация остановлена при завершении работы")

        if hasattr(self, 'signalr') and self.signalr_connected:
            self.signalr.disconnect()
            self.logger.info("Отключено от сервера при завершении работы")

        if hasattr(self, 'db') and hasattr(self.db, 'conn') and self.db.conn and not self.db.conn.closed:
            self.db.conn.close()
            self.logger.info("Подключение к БД закрыто при завершении работы")

        self.logger.info("Завершение работы приложения")
        event.accept()