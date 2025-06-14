import logging

from src.config import config

# Global Logger
logging.basicConfig(filename=config.LOG_PATH, level=logging.DEBUG)
logger = logging.getLogger(__name__)
