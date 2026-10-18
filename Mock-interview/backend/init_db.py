"""
Run this once to create all tables:  python3 init_db.py
(main.py also creates tables automatically on startup, so this is mostly
useful if you want to reset the schema during development.)
"""

from database import engine, Base
import models  # noqa: F401 - registers models on Base

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print("Tables created:", list(Base.metadata.tables.keys()))
