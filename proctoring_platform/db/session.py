from typing import Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from proctoring_platform.core.config import get_settings
from proctoring_platform.db.base import Base

_engine: Optional[Engine] = None
_session_factory: Optional[sessionmaker] = None


def configure_database(database_url: str) -> Engine:
    global _engine, _session_factory

    engine_kwargs = {"future": True}
    if database_url.startswith("sqlite"):
        engine_kwargs["connect_args"] = {"check_same_thread": False}

    _engine = create_engine(database_url, **engine_kwargs)
    _session_factory = sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True)
    return _engine


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        configure_database(get_settings().database_url)
    assert _engine is not None
    return _engine


def init_db() -> None:
    # Import models so SQLAlchemy registers all metadata before create_all.
    import proctoring_platform.models  # noqa: F401

    Base.metadata.create_all(bind=get_engine())


def get_session() -> Session:
    global _session_factory
    if _session_factory is None:
        configure_database(get_settings().database_url)
    assert _session_factory is not None
    return _session_factory()


def get_db() -> Generator[Session, None, None]:
    db = get_session()
    try:
        yield db
    finally:
        db.close()
