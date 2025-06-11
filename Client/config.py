import os
import sys
from pathlib import Path
from dotenv import load_dotenv


def get_env_path():
    if getattr(sys, 'frozen', False):
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(sys.executable).parent

    env_path = base_path / ".env"
    if not env_path.exists():
        env_path = Path(__file__).parent.parent / ".env"
    return env_path


env_path = get_env_path()
load_dotenv(env_path)

class Config:
    SERVER_HOST = os.getenv("SERVER_HOST")
    SERVER_PORT = os.getenv("SERVER_PORT")
    SERVER_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"
    DB_SCHEMA = os.getenv("DB_SCHEMA", "public")
    DB_CONFIG = {
        "host": os.getenv("DB_HOST"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "dbname": os.getenv("DB_NAME"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD", ""),
        "options": f"-c search_path={os.getenv('DB_SCHEMA', 'public')}"
    }