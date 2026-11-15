"""
OCTS AI - Persistent Memory Repository
Provides transactional CRUD operations, query filtering, scoping enforcement,
and lifecycle management for MemoryRecord and ProjectRecord entities.
"""

from datetime import datetime, timezone
import json
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from backend.memory.memory_store import MemoryStore
from backend.memory.models import MemoryRecordORM, ProjectRecordORM
from backend.memory.schemas import (
    MemoryRecord,
    MemoryScope,
    MemorySource,
    MemoryStatus,
    MemoryType,
    MemoryUpdate,
    ProjectRecord,
    ProjectUpdate,
    utc_now,
)

logger = logging.getLogger("octs.memory.repository")


class MemoryRepository:
    """
    Data access repository for persistent memory storage.
    Guarantees strict user isolation and project boundary protection.
    """

    def __init__(self, store: Optional[MemoryStore] = None):
        self.store = store or MemoryStore()

    # --------------------------------------------------------------------------
    # Memory Record Operations
    # --------------------------------------------------------------------------

    def create_memory(self, record: MemoryRecord) -> MemoryRecord:
        """Persists a new memory record transactionally."""
        with self.store.session_scope() as session:
            orm_obj = MemoryRecordORM(
                memory_id=record.memory_id,
                owner_id=record.owner_id,
                memory_type=record.memory_type.value,
                scope=record.scope.value,
                discipline=record.discipline,
                project_id=record.project_id,
                session_id=record.session_id,
                content=record.content,
                structured_data_json=json.dumps(record.structured_data or {}),
                source=record.source.value,
                confidence=record.confidence,
                importance=record.importance,
                created_at=record.created_at,
                updated_at=record.updated_at,
                last_accessed_at=record.last_accessed_at,
                access_count=record.access_count,
                status=record.status.value,
                version=record.version,
                superseded_by=record.superseded_by,
            )
            session.add(orm_obj)
            session.flush()
            logger.debug(f"Created memory record {record.memory_id} (type={record.memory_type.value})")
            return record

    def get_memory(self, memory_id: str, owner_id: Optional[str] = None) -> Optional[MemoryRecord]:
        """Retrieves a single memory record by ID with optional owner verification."""
        with self.store.session_scope() as session:
            query = session.query(MemoryRecordORM).filter(MemoryRecordORM.memory_id == memory_id)
            if owner_id:
                query = query.filter(MemoryRecordORM.owner_id == owner_id)
            orm_obj = query.first()
            if not orm_obj:
                return None
            return self._to_pydantic_memory(orm_obj)

    def update_memory(
        self,
        memory_id: str,
        update: MemoryUpdate,
        owner_id: Optional[str] = None,
    ) -> Optional[MemoryRecord]:
        """Applies selective updates to a memory record."""
        with self.store.session_scope() as session:
            query = session.query(MemoryRecordORM).filter(MemoryRecordORM.memory_id == memory_id)
            if owner_id:
                query = query.filter(MemoryRecordORM.owner_id == owner_id)
            orm_obj = query.first()
            if not orm_obj:
                return None

            if update.content is not None:
                orm_obj.content = update.content
            if update.structured_data is not None:
                orm_obj.structured_data_json = json.dumps(update.structured_data)
            if update.status is not None:
                orm_obj.status = update.status.value
            if update.confidence is not None:
                orm_obj.confidence = update.confidence
            if update.importance is not None:
                orm_obj.importance = update.importance

            orm_obj.updated_at = utc_now()
            session.flush()
            return self._to_pydantic_memory(orm_obj)

    def delete_memory(
        self,
        memory_id: str,
        owner_id: Optional[str] = None,
        hard_delete: bool = False,
    ) -> bool:
        """Soft-deletes (or permanently purges) a memory record."""
        with self.store.session_scope() as session:
            query = session.query(MemoryRecordORM).filter(MemoryRecordORM.memory_id == memory_id)
            if owner_id:
                query = query.filter(MemoryRecordORM.owner_id == owner_id)
            orm_obj = query.first()
            if not orm_obj:
                return False

            if hard_delete:
                session.delete(orm_obj)
            else:
                orm_obj.status = MemoryStatus.DELETED.value
                orm_obj.updated_at = utc_now()
            session.flush()
            return True

    def archive_memory(self, memory_id: str, owner_id: Optional[str] = None) -> bool:
        """Marks a memory record as ARCHIVED."""
        with self.store.session_scope() as session:
            query = session.query(MemoryRecordORM).filter(MemoryRecordORM.memory_id == memory_id)
            if owner_id:
                query = query.filter(MemoryRecordORM.owner_id == owner_id)
            orm_obj = query.first()
            if not orm_obj:
                return False
            orm_obj.status = MemoryStatus.ARCHIVED.value
            orm_obj.updated_at = utc_now()
            session.flush()
            return True

    def supersede_memory(
        self,
        old_memory_id: str,
        new_record: MemoryRecord,
        owner_id: Optional[str] = None,
    ) -> MemoryRecord:
        """
        Marks old memory as superseded and links it to the newly created memory record.
        Maintains version progression without silent deletion.
        """
        with self.store.session_scope() as session:
            query = session.query(MemoryRecordORM).filter(MemoryRecordORM.memory_id == old_memory_id)
            if owner_id:
                query = query.filter(MemoryRecordORM.owner_id == owner_id)
            old_orm = query.first()
            if old_orm:
                old_orm.status = MemoryStatus.SUPERSEDED.value
                old_orm.superseded_by = new_record.memory_id
                old_orm.updated_at = utc_now()
                new_record.version = old_orm.version + 1

            new_orm = MemoryRecordORM(
                memory_id=new_record.memory_id,
                owner_id=new_record.owner_id,
                memory_type=new_record.memory_type.value,
                scope=new_record.scope.value,
                discipline=new_record.discipline,
                project_id=new_record.project_id,
                session_id=new_record.session_id,
                content=new_record.content,
                structured_data_json=json.dumps(new_record.structured_data or {}),
                source=new_record.source.value,
                confidence=new_record.confidence,
                importance=new_record.importance,
                created_at=new_record.created_at,
                updated_at=new_record.updated_at,
                last_accessed_at=new_record.last_accessed_at,
                access_count=new_record.access_count,
                status=new_record.status.value,
                version=new_record.version,
                superseded_by=None,
            )
            session.add(new_orm)
            session.flush()
            return new_record

    def list_memories(
        self,
        owner_id: str,
        project_id: Optional[str] = None,
        discipline: Optional[str] = None,
        memory_type: Optional[MemoryType] = None,
        status: Optional[MemoryStatus] = MemoryStatus.ACTIVE,
        limit: int = 50,
        offset: int = 0,
    ) -> List[MemoryRecord]:
        """Lists memories matching filters for a given owner."""
        with self.store.session_scope() as session:
            query = session.query(MemoryRecordORM).filter(MemoryRecordORM.owner_id == owner_id)

            if status is not None:
                query = query.filter(MemoryRecordORM.status == status.value)
            if project_id is not None:
                query = query.filter(MemoryRecordORM.project_id == project_id)
            if discipline is not None:
                query = query.filter(
                    or_(
                        MemoryRecordORM.discipline == discipline,
                        MemoryRecordORM.discipline.is_(None),
                    )
                )
            if memory_type is not None:
                query = query.filter(MemoryRecordORM.memory_type == memory_type.value)

            query = query.order_by(MemoryRecordORM.created_at.desc()).offset(offset).limit(limit)
            return [self._to_pydantic_memory(m) for m in query.all()]

    def query_retrieval_candidates(
        self,
        owner_id: str,
        project_id: Optional[str] = None,
        discipline: Optional[str] = None,
        min_confidence: float = 0.60,
    ) -> List[MemoryRecord]:
        """
        Retrieves active candidates eligible for prompt injection.
        Enforces strict multi-tier scope isolation:
        - Only status='active' memories are considered.
        - User-scope memories for the owner.
        - Discipline-scope memories only if discipline matches or is null.
        - Project-scope memories ONLY for the specified project_id.
        - Cross-project memories are strictly excluded.
        """
        with self.store.session_scope() as session:
            scope_conditions = []

            # 1. User-level preferences apply across projects
            scope_conditions.append(MemoryRecordORM.scope == MemoryScope.USER.value)

            # 2. Discipline-level preferences apply when discipline matches
            if discipline:
                scope_conditions.append(
                    and_(
                        MemoryRecordORM.scope == MemoryScope.DISCIPLINE.value,
                        or_(
                            MemoryRecordORM.discipline == discipline,
                            MemoryRecordORM.discipline.is_(None),
                        ),
                    )
                )
            else:
                scope_conditions.append(MemoryRecordORM.scope == MemoryScope.DISCIPLINE.value)

            # 3. Project-level memories ONLY if project_id is provided
            if project_id:
                scope_conditions.append(
                    and_(
                        MemoryRecordORM.scope == MemoryScope.PROJECT.value,
                        MemoryRecordORM.project_id == project_id,
                    )
                )

            query = session.query(MemoryRecordORM).filter(
                and_(
                    MemoryRecordORM.owner_id == owner_id,
                    MemoryRecordORM.status == MemoryStatus.ACTIVE.value,
                    MemoryRecordORM.confidence >= min_confidence,
                    or_(*scope_conditions),
                )
            )

            results = query.order_by(MemoryRecordORM.importance.desc(), MemoryRecordORM.updated_at.desc()).all()
            return [self._to_pydantic_memory(m) for m in results]

    def record_access(self, memory_ids: List[str]) -> None:
        """Updates last_accessed_at and increments access_count for retrieved memories."""
        if not memory_ids:
            return
        with self.store.session_scope() as session:
            now = utc_now()
            session.query(MemoryRecordORM).filter(
                MemoryRecordORM.memory_id.in_(memory_ids)
            ).update(
                {
                    MemoryRecordORM.last_accessed_at: now,
                    MemoryRecordORM.access_count: MemoryRecordORM.access_count + 1,
                },
                synchronize_session=False,
            )

    # --------------------------------------------------------------------------
    # Project Operations
    # --------------------------------------------------------------------------

    def create_project(self, project: ProjectRecord) -> ProjectRecord:
        """Persists a new project definition."""
        with self.store.session_scope() as session:
            orm_obj = ProjectRecordORM(
                project_id=project.project_id,
                owner_id=project.owner_id,
                name=project.name,
                description=project.description,
                discipline=project.discipline,
                metadata_json=json.dumps(project.metadata or {}),
                is_active=project.is_active,
                created_at=project.created_at,
                updated_at=project.updated_at,
            )
            session.add(orm_obj)
            session.flush()
            logger.info(f"Created project '{project.name}' (id={project.project_id})")
            return project

    def get_project(self, project_id: str, owner_id: Optional[str] = None) -> Optional[ProjectRecord]:
        """Retrieves a single project record by ID."""
        with self.store.session_scope() as session:
            query = session.query(ProjectRecordORM).filter(ProjectRecordORM.project_id == project_id)
            if owner_id:
                query = query.filter(ProjectRecordORM.owner_id == owner_id)
            orm_obj = query.first()
            if not orm_obj:
                return None
            return self._to_pydantic_project(orm_obj)

    def list_projects(self, owner_id: str, active_only: bool = True) -> List[ProjectRecord]:
        """Lists projects owned by a user."""
        with self.store.session_scope() as session:
            query = session.query(ProjectRecordORM).filter(ProjectRecordORM.owner_id == owner_id)
            if active_only:
                query = query.filter(ProjectRecordORM.is_active == True)
            query = query.order_by(ProjectRecordORM.updated_at.desc())
            return [self._to_pydantic_project(p) for p in query.all()]

    def update_project(
        self,
        project_id: str,
        update: ProjectUpdate,
        owner_id: Optional[str] = None,
    ) -> Optional[ProjectRecord]:
        """Applies updates to project definition."""
        with self.store.session_scope() as session:
            query = session.query(ProjectRecordORM).filter(ProjectRecordORM.project_id == project_id)
            if owner_id:
                query = query.filter(ProjectRecordORM.owner_id == owner_id)
            orm_obj = query.first()
            if not orm_obj:
                return None

            if update.name is not None:
                orm_obj.name = update.name
            if update.description is not None:
                orm_obj.description = update.description
            if update.discipline is not None:
                orm_obj.discipline = update.discipline
            if update.metadata is not None:
                orm_obj.metadata_json = json.dumps(update.metadata)
            if update.is_active is not None:
                orm_obj.is_active = update.is_active

            orm_obj.updated_at = utc_now()
            session.flush()
            return self._to_pydantic_project(orm_obj)

    def delete_project(self, project_id: str, owner_id: Optional[str] = None) -> bool:
        """Deactivates a project and archives associated project-scoped memories."""
        with self.store.session_scope() as session:
            query = session.query(ProjectRecordORM).filter(ProjectRecordORM.project_id == project_id)
            if owner_id:
                query = query.filter(ProjectRecordORM.owner_id == owner_id)
            orm_obj = query.first()
            if not orm_obj:
                return False

            orm_obj.is_active = False
            orm_obj.updated_at = utc_now()

            # Archive associated project memories
            session.query(MemoryRecordORM).filter(
                MemoryRecordORM.project_id == project_id
            ).update(
                {
                    MemoryRecordORM.status: MemoryStatus.ARCHIVED.value,
                    MemoryRecordORM.updated_at: utc_now(),
                },
                synchronize_session=False,
            )

            session.flush()
            return True

    # --------------------------------------------------------------------------
    # Helper Mappers
    # --------------------------------------------------------------------------

    @staticmethod
    def _to_pydantic_memory(orm_obj: MemoryRecordORM) -> MemoryRecord:
        return MemoryRecord(
            memory_id=orm_obj.memory_id,
            owner_id=orm_obj.owner_id,
            memory_type=MemoryType(orm_obj.memory_type),
            scope=MemoryScope(orm_obj.scope),
            discipline=orm_obj.discipline,
            project_id=orm_obj.project_id,
            session_id=orm_obj.session_id,
            content=orm_obj.content,
            structured_data=orm_obj.structured_data,
            source=MemorySource(orm_obj.source),
            confidence=orm_obj.confidence,
            importance=orm_obj.importance,
            created_at=orm_obj.created_at.replace(tzinfo=timezone.utc) if orm_obj.created_at.tzinfo is None else orm_obj.created_at,
            updated_at=orm_obj.updated_at.replace(tzinfo=timezone.utc) if orm_obj.updated_at.tzinfo is None else orm_obj.updated_at,
            last_accessed_at=orm_obj.last_accessed_at.replace(tzinfo=timezone.utc) if (orm_obj.last_accessed_at and orm_obj.last_accessed_at.tzinfo is None) else orm_obj.last_accessed_at,
            access_count=orm_obj.access_count,
            status=MemoryStatus(orm_obj.status),
            version=orm_obj.version,
            superseded_by=orm_obj.superseded_by,
        )

    @staticmethod
    def _to_pydantic_project(orm_obj: ProjectRecordORM) -> ProjectRecord:
        return ProjectRecord(
            project_id=orm_obj.project_id,
            owner_id=orm_obj.owner_id,
            name=orm_obj.name,
            description=orm_obj.description,
            discipline=orm_obj.discipline,
            metadata=orm_obj.metadata_dict,
            is_active=orm_obj.is_active,
            created_at=orm_obj.created_at.replace(tzinfo=timezone.utc) if orm_obj.created_at.tzinfo is None else orm_obj.created_at,
            updated_at=orm_obj.updated_at.replace(tzinfo=timezone.utc) if orm_obj.updated_at.tzinfo is None else orm_obj.updated_at,
        )
