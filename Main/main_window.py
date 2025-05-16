from PySide6.QtWidgets import QMainWindow, QMessageBox
from PySide6.QtCore import QTimer
from ui_telemetry_client import Ui_MainWindow
from ui import PacketTable
from core import SignalRClient, TelemetryApiClient
from postgres import PostgresManager
from models import TelemetryPacket
from config import Config
import json


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.signalr = SignalRClient(Config.SERVER_URL + "/telemetryhub")
        self.api = TelemetryApiClient(Config.SERVER_URL + "/api/Telemetry")
        self.db = PostgresManager(Config.DB_CONFIG)

        self.signalr_connected = False
        self.is_generation_active = False

        self.table = PacketTable()
        self.ui.verticalLayout.addWidget(self.table)
        self.status_bar = self.statusBar()
        self.ui.btnStart.setToolTip("Запускает генерацию и передачу телеметрических данных")
        self.ui.btnStop.setToolTip("Приостанавливает генерацию данных")

        self.db_check_timer = QTimer()
        self.server_check_timer = QTimer()

        self.setup_connections()
        self.setup_timers()
        self.update_ui_state()

    def setup_connections(self):
        self.signalr.on_packet_received(self.handle_new_packet)
        self.ui.btnConnect.clicked.connect(self.toggle_connection)
        self.ui.btnStart.clicked.connect(self.start_generation)
        self.ui.btnStop.clicked.connect(self.stop_generation)

        self.signalr.connection.on_open(self.on_connected)
        self.signalr.connection.on_close(self.on_disconnected)
        self.signalr.connection.on_error(lambda err: print(f"SignalR error: {err}"))

    def setup_timers(self):
        self.db_check_timer.timeout.connect(self.check_db_notifications)
        self.db_check_timer.start(1000)

        self.server_check_timer.timeout.connect(self.check_server_status)
        self.server_check_timer.start(5000)

    def handle_new_packet(self, packet):
        try:
            packet = self.parse_packet(packet)
            if packet:
                self.table.add_packet(packet)
        except Exception as e:
            print(f"Ошибка обработки пакета: {e}")

    def parse_packet(self, raw_packet):
        if isinstance(raw_packet, str):
            try:
                raw_packet = json.loads(raw_packet)
            except json.JSONDecodeError:
                return None

        if isinstance(raw_packet, list) and len(raw_packet) > 0:
            raw_packet = raw_packet[0]

        if not isinstance(raw_packet, dict):
            return None

        try:
            return TelemetryPacket(
                id=raw_packet.get('id', 0),
                counter=raw_packet.get('packetCounter', 0),
                timestamp=raw_packet.get('timestamp', 0),
                payload=raw_packet.get('payload', 0.0),
                crc16=raw_packet.get('crc16', 0),
                status='NegativeValue' if raw_packet.get('payload', 0) < 0 else 'OK'
            )
        except Exception:
            return None

    def check_db_notifications(self):
        if notification := self.db.get_notifications():
            if packet := self.db.get_packet(int(notification.payload)):
                self.handle_new_packet(packet)

    def check_server_status(self):
        try:
            http_ok = self.api.get_status().status_code == 200
            status_parts = [
                "HTTP: OK" if http_ok else "HTTP: ERROR",
                f"SignalR: {'CONNECTED' if self.signalr_connected else 'DISCONNECTED'}"
            ]
            self.status_bar.showMessage(" | ".join(status_parts))
        except Exception:
            self.status_bar.showMessage("Сервер недоступен")

    def toggle_connection(self):
        if self.signalr_connected:
            self.signalr.disconnect()
        else:
            self.signalr.connect()

    def start_generation(self):
        if not self.signalr_connected:
            self.show_error("Сначала подключитесь к серверу")
            return

        try:
            self.current_counter = 0
            response = self.api.start_generation()
            if response.status_code == 200:
                self.is_generation_active = True
                self.update_ui_state()
        except Exception as e:
            self.show_error(f"Ошибка запуска: {e}")

    def stop_generation(self):
        try:
            response = self.api.stop_generation()
            if response.status_code == 200:
                self.is_generation_active = False
                self.update_ui_state()
        except Exception as e:
            self.show_error(f"Ошибка остановки: {e}")

    def on_connected(self):
        self.signalr_connected = True
        self.db.listen_channel("new_packet")
        self.update_ui_state()
        self.status_bar.showMessage("SignalR подключен", 3000)

    def on_disconnected(self):
        self.signalr_connected = False
        self.is_generation_active = False
        self.update_ui_state()
        self.status_bar.showMessage("SignalR отключен", 3000)

    def update_ui_state(self):
        self.ui.btnConnect.setText("Отключиться" if self.signalr_connected else "Подключиться к серверу")
        self.ui.btnStart.setEnabled(self.signalr_connected and not self.is_generation_active)
        self.ui.btnStop.setEnabled(self.is_generation_active)
        self.status_bar.showMessage(f"Генерация: {'ВКЛ' if self.is_generation_active else 'ВЫКЛ'}")

    def show_error(self, message):
        QMessageBox.critical(self, "Ошибка", message)
        self.status_bar.showMessage(f"Ошибка: {message}", 5000)

    def closeEvent(self, event):
        self.signalr.disconnect()
        self.db.conn.close()
        self.db_check_timer.stop()
        self.server_check_timer.stop()
        event.accept()