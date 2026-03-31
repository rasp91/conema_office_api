from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, MetaData

from src.config import config

# Init Metadata
metadata = MetaData()

# Database Instance
DATABASE_URL = (
    f"mysql+pymysql://{config.DATABASE_USER}:{config.DATABASE_SECRET}@{config.DATABASE_HOST}/{config.DATABASE_NAME}?charset=utf8mb4"
)

# Create Engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # FIX dead connections
    pool_recycle=1800,  # FIX MySQL idle timeout (30 min)
    # pool_size=10,
    # max_overflow=20,
)

# Create Session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
