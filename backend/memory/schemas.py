"""
OCTS AI - Memory & Persistent Intelligence Schemas
Defines strongly typed Pydantic models for memory records, projects,
scopes, extraction payloads, and retrieval telemetry.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MemoryType(str, Enum):
    """Classification categories for persistent memories."""
    USER_PREFERENCE = "user_preference"
    PROJECT = "project"
    DECISION = "decision"
    CONSTRAINT = "constraint"
    INTERACTION_CONTEXT = "interaction_context"


class MemoryScope(str, Enum):
    """Access boundaries determining where memory can be retrieved."""
    USER = "user"
    DISCIPLINE = "discipline"
    PROJECT = "project"
    SESSION = "session"


class MemoryStatus(str, Enum):
    """Lifecycle states of a memory record."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    SUPERSEDED = "superseded"
    DELETED = "deleted"


class MemorySource(str, Enum):
    """Provenance tracking how the memory was originated."""
    EXPLICIT_USER = "explicit_user"
    INFERRED_AGENT = "inferred_agent"
    SYSTEM_RULE = "system_rule"
    CONSOLIDATED = "consolidated"


def utc_now() -> datetime:
    """Returns current timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


class MemoryRecord(BaseModel):
    """
    Strongly typed persistent memory entity.
    Maintains provenance, confidence, importance, versioning, and lifecycle status.
    """
    model_config = ConfigDict(extra="ignore")

    memory_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for the memory record.")
    owner_id: str = Field(default="default_user", description="Identifier of the owning user or tenant.")
    memory_type: MemoryType = Field(..., description="Classification category.")
    scope: MemoryScope = Field(default=MemoryScope.USER, description="Isolation scope.")
    discipline: Optional[str] = Field(default=None, description="Discipline identifier (writers, musicians, creators, designers) if discipline-scoped.")
    project_id: Optional[str] = Field(default=None, description="Associated project ID if project-scoped.")
    session_id: Optional[str] = Field(default=None, description="Associated session ID if session-scoped.")
    content: str = Field(..., min_length=1, max_length=10000, description="Clear, factual human-readable representation of the memory.")
    structured_data: Dict[str, Any] = Field(default_factory=dict, description="Typed metadata dictionary supporting key-value lookup.")
    source: MemorySource = Field(default=MemorySource.INFERRED_AGENT, description="Provenance source.")
    confidence: float = Field(default=0.85, ge=0.0, le=1.0, description="Confidence level in the accuracy of this memory.")
    importance: float = Field(default=0.70, ge=0.0, le=1.0, description="Priority weight for retrieval ranking.")
    created_at: datetime = Field(default_factory=utc_now, description="Timestamp of creation (UTC).")
    updated_at: datetime = Field(default_factory=utc_now, description="Timestamp of last modification (UTC).")
    last_accessed_at: Optional[datetime] = Field(default=None, description="Timestamp when last retrieved into context.")
    access_count: int = Field(default=0, ge=0, description="Total number of times retrieved.")
    status: MemoryStatus = Field(default=MemoryStatus.ACTIVE, description="Lifecycle status.")
    version: int = Field(default=1, ge=1, description="Version counter.")
    superseded_by: Optional[str] = Field(default=None, description="Memory ID that replaced this record if superseded.")

    @field_validator("discipline")
    @classmethod
    def validate_discipline(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            clean = v.strip().lower()
            allowed = {"writers", "musicians", "creators", "designers", "general"}
            if clean not in allowed:
                raise ValueError(f"Invalid discipline '{v}'. Allowed: {', '.join(sorted(allowed))}")
            return clean
        return v

    @field_validator("content")
    @classmethod
    def validate_content_not_empty(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Memory content cannot be empty or solely whitespace.")
        return s


class ProjectRecord(BaseModel):
    """
    Project metadata entity anchoring project-scoped memories.
    """
    model_config = ConfigDict(extra="ignore")

    project_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique project identifier.")
    owner_id: str = Field(default="default_user", description="Identifier of the project owner.")
    name: str = Field(..., min_length=1, max_length=200, description="Display name of the project.")
    description: Optional[str] = Field(default=None, max_length=2000, description="Creative goal and project summary.")
    discipline: Optional[str] = Field(default=None, description="Primary creative discipline of the project.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary project configuration metadata.")
    is_active: bool = Field(default=True, description="Whether the project is active.")
    created_at: datetime = Field(default_factory=utc_now, description="Creation timestamp (UTC).")
    updated_at: datetime = Field(default_factory=utc_now, description="Last update timestamp (UTC).")


class MemoryCreate(BaseModel):
    """Payload schema for creating a new memory record via API."""
    model_config = ConfigDict(extra="ignore")

    memory_type: MemoryType
    content: str = Field(..., min_length=1, max_length=10000)
    scope: MemoryScope = MemoryScope.USER
    discipline: Optional[str] = None
    project_id: Optional[str] = None
    structured_data: Dict[str, Any] = Field(default_factory=dict)
    source: MemorySource = MemorySource.EXPLICIT_USER
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    importance: float = Field(default=0.8, ge=0.0, le=1.0)


class MemoryUpdate(BaseModel):
    """Payload schema for updating an existing memory record."""
    model_config = ConfigDict(extra="ignore")

    content: Optional[str] = Field(default=None, min_length=1, max_length=10000)
    structured_data: Optional[Dict[str, Any]] = None
    status: Optional[MemoryStatus] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    importance: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class ProjectCreate(BaseModel):
    """Payload schema for creating a project."""
    model_config = ConfigDict(extra="ignore")

    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    discipline: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProjectUpdate(BaseModel):
    """Payload schema for updating a project."""
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    discipline: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class RetrievedMemoryItem(BaseModel):
    """Compact summary of a retrieved memory record included in response telemetry."""
    model_config = ConfigDict(extra="ignore")

    memory_id: str
    memory_type: str
    content: str
    relevance_score: float
    retrieval_reason: str


class MemoryMetadata(BaseModel):
    """
    Public telemetry metadata payload returned in PromptResponse.memory.
    """
    model_config = ConfigDict(extra="ignore")

    enabled: bool = Field(default=True, description="Whether memory subsystem was active for this request.")
    retrieval_performed: bool = Field(default=False, description="Whether memory query was executed.")
    memories_used: int = Field(default=0, ge=0, description="Count of memories injected into specialist context.")
    extraction_performed: bool = Field(default=False, description="Whether automatic extraction was executed.")
    persistence_status: str = Field(default="not_attempted", description="Persistence outcome: success | failed | skipped | not_attempted.")
    memories_retrieved: List[RetrievedMemoryItem] = Field(default_factory=list, description="List of memories retrieved and used.")
    project_id: Optional[str] = Field(default=None, description="Active project ID bound to this execution.")
    error_message: Optional[str] = Field(default=None, description="Sanitized error description if a memory operation failed.")
