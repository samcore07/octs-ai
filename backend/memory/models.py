"""
OCTS AI - SQLAlchemy Models for Persistent Memory & Projects
Defines table schemas, primary keys, relationships, and composite query indexes.
"""

from datetime import datetime, timezone
import json
from typing import Any, Dict

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class MemoryRecordORM(Base):
    """
    SQLAlchemy ORM table mapping for persistent creative memory records.
    """
    __tablename__ = "memory_records"

    memory_id = Column(String(36), primary_key=True, index=True)
    owner_id = Column(String(128), nullable=False, index=True)
    memory_type = Column(String(32), nullable=False, index=True)
    scope = Column(String(32), nullable=False, index=True)
    discipline = Column(String(32), nullable=True, index=True)
    project_id = Column(String(36), nullable=True, index=True)
    session_id = Column(String(128), nullable=True, index=True)
    content = Column(Text, nullable=False)
    structured_data_json = Column(Text, nullable=False, default="{}")
    source = Column(String(32), nullable=False)
    confidence = Column(Float, nullable=False, default=1.0)
    importance = Column(Float, nullable=False, default=0.7)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    last_accessed_at = Column(DateTime, nullable=True)
    access_count = Column(Integer, nullable=False, default=0)
    status = Column(String(32), nullable=False, index=True, default="active")
    version = Column(Integer, nullable=False, default=1)
    superseded_by = Column(String(36), nullable=True)

    __table_args__ = (
        Index("ix_memory_owner_status", "owner_id", "status"),
        Index("ix_memory_project_status", "project_id", "status"),
        Index("ix_memory_owner_type", "owner_id", "memory_type"),
        Index("ix_memory_owner_discipline", "owner_id", "discipline"),
    )

    @property
    def structured_data(self) -> Dict[str, Any]:
        try:
            return json.loads(self.structured_data_json) if self.structured_data_json else {}
        except Exception:
            return {}

    @structured_data.setter
    def structured_data(self, val: Dict[str, Any]):
        self.structured_data_json = json.dumps(val or {})


class ProjectRecordORM(Base):
    """
    SQLAlchemy ORM table mapping for creative project definitions.
    """
    __tablename__ = "projects"

    project_id = Column(String(36), primary_key=True, index=True)
    owner_id = Column(String(128), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    discipline = Column(String(32), nullable=True)
    metadata_json = Column(Text, nullable=False, default="{}")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

    __table_args__ = (
        Index("ix_project_owner_active", "owner_id", "is_active"),
    )

    @property
    def metadata_dict(self) -> Dict[str, Any]:
        try:
            return json.loads(self.metadata_json) if self.metadata_json else {}
        except Exception:
            return {}

    @metadata_dict.setter
    def metadata_dict(self, val: Dict[str, Any]):
        self.metadata_json = json.dumps(val or {})
