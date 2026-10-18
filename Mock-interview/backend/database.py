import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv(Path(__file__).resolve().parent / ".env")

DATABASE_URL = os.getenv(
    "DATABASE_URL", "mysql+mysqlconnector://root:root@localhost:3306/interview_mock_db"
)

# pool_pre_ping avoids "server closed the connection" errors after idle periods
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def masked_database_url() -> str:
    """DATABASE_URL with the password blanked out, safe to print/log."""
    if "@" not in DATABASE_URL or "://" not in DATABASE_URL:
        return DATABASE_URL
    scheme_and_creds, host_part = DATABASE_URL.rsplit("@", 1)
    scheme, creds = scheme_and_creds.split("://", 1)
    user = creds.split(":", 1)[0] if ":" in creds else creds
    return f"{scheme}://{user}:****@{host_part}"


def get_db():
    """FastAPI dependency that yields a DB session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
