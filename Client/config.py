import os
import sys
from pathlib import Path
from dotenv import load_dotenv


class Config:
    _env_loaded = False

    @classmethod
    def load_env(cls):
        if cls._env_loaded:
            return

        env_path = Path(__file__).parent.parent / ".env"
        if not env_path.exists():
            env_path = Path(sys.executable).parent / ".env"

        if env_path.exists():
            load_dotenv(env_path)

        cls.SERVER_HOST = os.getenv("SERVER_HOST", "localhost")
        cls.SERVER_PORT = os.getenv("SERVER_PORT", "5000")
        cls.SERVER_URL = "http://%s:%s" % (cls.SERVER_HOST, cls.SERVER_PORT)

        cls.DB_CONFIG = {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", "5432")),
            "dbname": os.getenv("DB_NAME", "telemetry"),
            "user": os.getenv("DB_USER", "postgres"),
            "password": os.getenv("DB_PASSWORD", ""),
            "options": "-c search_path=%s" % os.getenv('DB_SCHEMA', 'public')
        }

        cls._env_loaded = True