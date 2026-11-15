# OCTS AI — Phase 6: Storage Layer & Persistence Architecture

## 1. Storage Technology Rationale

The storage layer is implemented using **SQLAlchemy ORM** targeting **SQLite**.

### Why SQLite with SQLAlchemy?
1. **Zero External Daemon Dependencies**: Works out-of-the-box in local environments, CI/CD runners, and containerized deployments without requiring a separate PostgreSQL, MySQL, or Redis service.
2. **ACID Transactional Atomicity**: Database sessions guarantee that version increments, superseding links, and project archiving execute atomically within a single commit or rollback.
3. **Multi-Thread Concurrency**: Initialized with `connect_args={"check_same_thread": False}` to support FastAPI threadpool workers safely.
4. **Migration Ready**: SQLAlchemy declarative models can transition to PostgreSQL by updating `MEMORY_DATABASE_URL` in `.env` without altering repository code.

---

## 2. Relational Schema & ORM Mapping

### `memories` Table
```sql
CREATE TABLE memories (
    memory_id VARCHAR(64) PRIMARY KEY,
    owner_id VARCHAR(128) NOT NULL,
    memory_type VARCHAR(32) NOT NULL,
    scope VARCHAR(32) NOT NULL,
    discipline VARCHAR(64),
    project_id VARCHAR(64),
    session_id VARCHAR(64),
    content TEXT NOT NULL,
    structured_data TEXT DEFAULT '{}',
    source VARCHAR(32) DEFAULT 'explicit_user',
    confidence FLOAT DEFAULT 0.85,
    importance FLOAT DEFAULT 0.70,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_accessed_at TIMESTAMP WITH TIME ZONE,
    access_count INTEGER DEFAULT 0,
    status VARCHAR(32) DEFAULT 'active',
    version INTEGER DEFAULT 1,
    superseded_by VARCHAR(64),
    FOREIGN KEY(project_id) REFERENCES projects(project_id)
);
```

### Composite Indexes for Query Optimization
To ensure constant-time filtering across thousands of memory items, the schema defines five composite indexes:
- `ix_memory_owner_status`: `(owner_id, status)` — Fast filtering for active user memories.
- `ix_memory_project_status`: `(project_id, status)` — Fast project-scoped retrieval.
- `ix_memory_owner_type`: `(owner_id, memory_type)` — Type-specific listing and consolidation lookups.
- `ix_memory_owner_discipline`: `(owner_id, discipline)` — Discipline-aligned candidate retrieval.
- `ix_project_owner_active`: `(owner_id, is_active)` — Fast active project lookups.

### `projects` Table
```sql
CREATE TABLE projects (
    project_id VARCHAR(64) PRIMARY KEY,
    owner_id VARCHAR(128) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    discipline VARCHAR(64),
    metadata_json TEXT DEFAULT '{}',
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL
);
```

---

## 3. Session & Connection Management

`MemoryStore` encapsulates the engine lifecycle and provides an atomic context manager:

```python
@contextmanager
def session_scope(self) -> Generator[Session, None, None]:
    """Provides a transactional scope around a series of operations."""
    session = self.session_factory()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
```
