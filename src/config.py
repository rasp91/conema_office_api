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
    DATABASE_KEY: str
    DATABASE_DEFAULT_PASSWORD: str

    # Logs
    ROOT_PATH: str
    LOG_PATH: str = ""
    DATA_PATH: str = ""

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int
    JWT_ACCESS_TOKEN_EXPIRE_DAYS: int

    def init(self):
        self.LOG_PATH = os.path.join(self.ROOT_PATH, "global.log")
        self.DATA_PATH = os.path.join(self.DATA_PATH, "data")

        # Init Data Path
        if not os.path.exists(self.DATA_PATH):
            os.makedirs(self.DATA_PATH)


config = Config()
config.init()
