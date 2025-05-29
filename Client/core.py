import json
import requests
from requests.adapters import HTTPAdapter
from signalrcore.hub_connection_builder import HubConnectionBuilder
from urllib3 import Retry
from typing import Callable


class SignalRClient:
    def __init__(self, url: str):
        connection_builder = HubConnectionBuilder()
        connection_builder.with_url(url)
        connection_builder.with_automatic_reconnect({
            "type": "interval",
            "keep_alive_interval": 10,
            "reconnect_interval": 30,
            "max_attempts": 3
        })
        self.connection = connection_builder.build()

    def connect(self):
        self.connection.start()

    def disconnect(self):
        self.connection.stop()

    def on_packet_received(self, callback: Callable):
        self.connection.on("NewPacket", callback)


class TelemetryApiClient:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        self._session = self._create_session()

    @classmethod
    def _create_session(cls):
        session = requests.Session()
        retry = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session

    def get_status(self):
        return self._session.get(f"{self.base_url}/status", timeout=5)

    # def get_sessions(self):
    #     response = self._session.get(f"{self.base_url}/sessions", timeout=10)
    #     response.raise_for_status()
    #     return response.json() if response.text.strip() else []
    #
    # def get_session_packets(self, session_id):
    #     endpoints = [
    #         f"/sessions/{session_id}/packets",
    #         f"/session/{session_id}/telemetry",
    #         f"/api/sessions/{session_id}/data"
    #     ]
    #
    #     for endpoint in endpoints:
    #         try:
    #             response = self._session.get(f"{self.base_url}{endpoint}", timeout=10)
    #             if response.status_code == 200:
    #                 return response.json()
    #             response.raise_for_status()
    #         except Exception:
    #             continue
    #     return []

    def start_session(self, name):
        response = self._session.post(
            f"{self.base_url}/sessions/start",
            json={"name": name},
            timeout=10
        )
        response.raise_for_status()

        data = response.json()
        session_id = data.get('SessionId') or data.get('sessionId') or data.get('id')
        response._content = json.dumps({'SessionId': session_id}).encode()
        return response

    def start_generation(self, session_id):
        return self._session.post(
            f"{self.base_url}/start",
            json={"sessionId": session_id},
            timeout=10
        )

    def stop_generation(self):
        return self._session.post(f"{self.base_url}/stop", timeout=2)

    def end_session(self):
        return self._session.post(f"{self.base_url}/sessions/end", timeout=2)
