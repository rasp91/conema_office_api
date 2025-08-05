import logging
import sys

from src.config import config

# Create a custom logger
logger = logging.getLogger("roechling_office_api")
logger.setLevel(logging.DEBUG)

# Prevent duplicate logs by clearing existing handlers
if logger.handlers:
    logger.handlers.clear()

# Create formatters
console_formatter = logging.Formatter(fmt="%(asctime)s | %(name)s | %(levelname)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

file_formatter = logging.Formatter(
    fmt="%(asctime)s | %(name)s | %(levelname)s | %(filename)s:%(lineno)d | %(funcName)s() | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)

# Create console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(console_formatter)

# Create file handler
file_handler = logging.FileHandler(config.LOG_PATH, encoding="utf-8")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(file_formatter)

# Add handlers to logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Prevent propagation to root logger to avoid duplicate logs
logger.propagate = False
