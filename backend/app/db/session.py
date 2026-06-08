from collections.abc import Generator
from pathlib import Path

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def create_app_engine(database_url: str | None = None) -> Engine:
    url = resolve_sqlite_database_url(database_url or settings.database_url)
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=connect_args, future=True)


def resolve_sqlite_database_url(database_url: str) -> str:
    for prefix in ("sqlite:///", "sqlite+pysqlite:///"):
        if not database_url.startswith(prefix):
            continue
        raw_path = database_url.removeprefix(prefix)
        db_path, separator, suffix = raw_path.partition("?")
        if db_path in {"", ":memory:"} or Path(db_path).is_absolute():
            return database_url
        absolute_path = (PROJECT_ROOT / db_path).resolve()
        return f"{prefix}{absolute_path}{separator}{suffix}"
    return database_url


def create_session_factory(database_url: str | None = None) -> sessionmaker[Session]:
    return sessionmaker(
        bind=create_app_engine(database_url),
        autoflush=False,
        autocommit=False,
        future=True,
    )


def get_db() -> Generator[Session, None, None]:
    session_local = create_session_factory(settings.api_database_url)
    db = session_local()
    try:
        yield db
    finally:
        db.close()
