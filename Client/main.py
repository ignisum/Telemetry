import sys
from config import Config
from logging_config import setup_logging
from PySide6.QtWidgets import QApplication
from main_window import MainWindow


if __name__ == "__main__":
    Config.load_env()
    setup_logging()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())