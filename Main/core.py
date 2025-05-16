from signalrcore.hub_connection_builder import HubConnectionBuilder
import requests
from typing import Callable


class SignalRClient:
    def __init__(self, url: str):
        self.connection = HubConnectionBuilder() \
            .with_url(url) \
            .with_automatic_reconnect({
            "type": "interval",
            "keep_alive_interval": 10,
            "reconnect_interval": 5,
            "max_attempts": 5
        }).build()

    def connect(self):
        self.connection.start()

    def disconnect(self):
        self.connection.stop()

    def on_packet_received(self, callback: Callable):
        self.connection.on("NewPacket", callback)


class TelemetryApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def start_generation(self):
        return requests.post(f"{self.base_url}/start", timeout=2)

    def stop_generation(self):
        return requests.post(f"{self.base_url}/stop", timeout=2)

    def get_status(self):
        return requests.get(f"{self.base_url}/status", timeout=2)