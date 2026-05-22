"""
database.py — SQLite/PostgreSQL baglanti yonetimi
Varsayilan SQLite, opsiyonel PostgreSQL (env var ile).
"""
import os
from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, Boolean
from sqlalchemy.orm import sessionmaker
from PYTHON.risk.models import Base


def get_engine():
    """DATABASE_URL env var'i varsa PostgreSQL, yoksa SQLite kullanir."""
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return create_engine(db_url, echo=False, pool_pre_ping=True)
    # Varsayilan: SQLite
    db_path = os.getenv("SQLITE_PATH", "anatoliax.db")
    return create_engine(f"sqlite:///{db_path}", echo=False)


def init_db(engine=None):
    """Tum tablolari olusturur."""
    if engine is None:
        engine = get_engine()
    Base.metadata.create_all(engine)
    return engine


def get_session(engine=None):
    """Yeni bir session olusturur."""
    if engine is None:
        engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()
