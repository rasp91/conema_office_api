import os

from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env file
if not os.path.isfile(os.path.join("\\".join(os.path.abspath(__file__).split("\\")[:-2]), ".env")):
    raise FileNotFoundError(".env config file not found")
load_dotenv(dotenv_path=".env", override=True)


class Config(BaseSettings):
    # API
    API_KEY: str

    # Database
    DATABASE_HOST: str
    DATABASE_NAME: str
    DATABASE_USER: str
    DATABASE_SECRET: str

    # Paths
    ROOT_PATH: str
    LOGS_PATH: str = ""
    DATA_PATH: str = ""

    # Logs
    GLOBAL_LOG_PATH: str = ""
    APP_LOG_PATH: str = ""

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int
    JWT_ACCESS_TOKEN_EXPIRE_DAYS: int

    def init(self):
        # Paths
        self.LOGS_PATH = os.path.join(self.ROOT_PATH, "logs")
        self.DATA_PATH = os.path.join(self.ROOT_PATH, "data")

        # Logs
        self.GLOBAL_LOG_PATH = os.path.join(self.LOGS_PATH, "global.log")
        self.APP_LOG_PATH = os.path.join(self.LOGS_PATH, "app.log")

        # Init Paths
        os.makedirs(self.LOGS_PATH, exist_ok=True)
        os.makedirs(self.DATA_PATH, exist_ok=True)
        os.makedirs(os.path.join(self.DATA_PATH, "news", "thumbnails"), exist_ok=True)
        os.makedirs(os.path.join(self.DATA_PATH, "news", "images"), exist_ok=True)
        os.makedirs(os.path.join(self.DATA_PATH, "news", "files"), exist_ok=True)


config = Config()
config.init()
