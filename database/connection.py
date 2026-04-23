from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker

from config.settings import get_settings

_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        database_url = settings.database_url
        if not database_url:
            raise RuntimeError("DATABASE_URL not set")
        _engine = create_engine(
            database_url,
            pool_pre_ping=True,
            pool_recycle=300,
            echo=False,
        )
    return _engine


def get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), autocommit=False, autoflush=False)
    return _SessionLocal


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Context manager that yields a DB session and handles commit/rollback."""
    SessionLocal = get_session_factory()
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def execute_query(sql: str, params: dict | None = None) -> list[dict]:
    """Execute a raw SQL string and return rows as list of dicts."""
    try:
        with get_db() as session:
            result = session.execute(text(sql), params or {})
            if result.returns_rows:
                return [dict(row) for row in result.mappings().all()]
            return []
    except OperationalError:
        return []


def test_connection() -> bool:
    try:
        with get_db() as session:
            session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
