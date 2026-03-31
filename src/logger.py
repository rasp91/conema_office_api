import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler

from src.config import config

# Ensure logs directory exists before any handler tries to open a file
os.makedirs(config.LOGS_PATH, exist_ok=True)

# Formatters
CONSOLE_FORMATTER = logging.Formatter(
    fmt="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
FILE_FORMATTER = logging.Formatter(
    fmt="%(asctime)s | %(name)s | %(levelname)s | %(filename)s:%(lineno)d | %(funcName)s() | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# --- Root logger → global.log (catches all loggers including third-party) ---
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
if not root_logger.handlers:
    global_handler = logging.FileHandler(config.GLOBAL_LOG_PATH, encoding="utf-8")
    global_handler.setFormatter(FILE_FORMATTER)
    root_logger.addHandler(global_handler)

# --- App logger → app.YYYYMMDD.log + console ---
app_logger = logging.getLogger("roechling_office_api")
app_logger.setLevel(logging.INFO)

if not app_logger.handlers:
    # Rotating file handler: daily rotation, 5 backups, pattern: app.20250131.log
    file_handler = TimedRotatingFileHandler(
        config.APP_LOG_PATH, when="midnight", interval=1, backupCount=5, encoding="utf-8"
    )
    file_handler.suffix = "%Y%m%d.log"
    file_handler.setFormatter(FILE_FORMATTER)
    app_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(CONSOLE_FORMATTER)
    app_logger.addHandler(console_handler)
