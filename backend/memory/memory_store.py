"""
OCTS AI - Persistent Memory Database Engine & Session Factory
Initializes SQLite connection pool, provides transactional sessions,
and handles schema creation.
"""

from contextlib import contextmanager
import logging
from typing import Generator, Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.memory.config import MemorySettings
from backend.memory.models import Base

logger = logging.getLogger("octs.memory.store")


class MemoryStore:
    """
    Encapsulates the database connection, engine lifecycle, and session generation.
    """

    def __init__(self, settings: Optional[MemorySettings] = None, database_url: Optional[str] = None):
        self.settings = settings or MemorySettings()
        self.db_url = database_url or self.settings.memory_database_url

        connect_args = {}
        if self.db_url.startswith("sqlite"):
            # Enable SQLite multi-threaded access for FastAPI async/threadpool handlers
            connect_args["check_same_thread"] = False

        self.engine = create_engine(
            self.db_url,
            connect_args=connect_args,
            pool_pre_ping=True,
        )
        self.session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
            expire_on_commit=False,
        )
        self.init_db()

    def init_db(self) -> None:
        """Creates tables and indexes if they do not exist."""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info(f"Initialized persistent memory store at '{self.db_url}'.")
        except Exception as e:
            logger.error(f"Failed to initialize memory database tables: {e}", exc_info=True)
            raise

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """Transactional session context manager with automatic rollback on error."""
        session: Session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_session(self) -> Session:
        """Returns a new raw session instance (caller must manage lifecycle)."""
        return self.session_factory()
