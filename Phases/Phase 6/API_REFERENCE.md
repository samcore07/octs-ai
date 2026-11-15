# OCTS AI — Phase 6: REST API Reference & Contracts

## 1. Projects Endpoints

All project routes are mounted at `/api/memory/projects` (registered before `/api/memory/{memory_id}` to prevent path collisions).

### `GET /api/memory/projects`
Lists active projects for the authenticated caller.
- **Headers**: `X-User-Id` (optional, defaults to `default_user`).
- **Response**: `200 OK`
```json
[
  {
    "project_id": "proj_12345",
    "owner_id": "user_abc",
    "name": "Neon Syndicate",
    "description": "Cyberpunk narrative thriller series.",
    "discipline": "writers",
    "is_active": true,
    "created_at": "2026-11-15T10:00:00Z",
    "updated_at": "2026-11-15T10:00:00Z"
  }
]
```

### `POST /api/memory/projects`
Creates a new creative project.
- **Status**: `201 Created`
- **Request Body**:
```json
{
  "name": "Soundtrack Horizon",
  "description": "Cinematic synthwave concept album.",
  "primary_discipline": "musicians"
}
```

### `GET /api/memory/projects/{project_id}`
Retrieves a single project by ID.
- **Status**: `200 OK` (or `404 Not Found`).

### `PATCH /api/memory/projects/{project_id}`
Updates project name or description.
- **Status**: `200 OK`.

### `DELETE /api/memory/projects/{project_id}`
Deactivates a project and automatically archives all associated project-scoped memories.
- **Status**: `200 OK`.

---

## 2. Memory Records Endpoints

### `GET /api/memory`
Lists memory records with optional filters.
- **Query Parameters**:
  * `project_id`: Filter by specific project.
  * `discipline`: Filter by discipline (`writers`, `musicians`, etc.).
  * `memory_type`: Filter by type (`constraint`, `user_preference`, etc.).
  * `status`: Filter by lifecycle state (`active`, `archived`, `superseded`, `deleted`).
  * `limit`: Page size (default 50).
  * `offset`: Page offset (default 0).
- **Status**: `200 OK`.

### `POST /api/memory`
Explicitly creates a persistent memory record.
- **Status**: `201 Created`.
- **Request Body**:
```json
{
  "memory_type": "constraint",
  "scope": "discipline",
  "discipline": "writers",
  "content": "Never use purple prose in mystery dialogue.",
  "confidence": 0.95,
  "importance": 0.90
}
```

### `GET /api/memory/{memory_id}`
Retrieves a single memory record.
- **Status**: `200 OK` (or `404 Not Found`).

### `PATCH /api/memory/{memory_id}`
Updates memory content, importance, or status.
- **Status**: `200 OK`.

### `DELETE /api/memory/{memory_id}`
Soft-deletes a memory record (`status="deleted"`).
- **Status**: `200 OK`.

---

## 3. Orchestration API Integration (`POST /ask`)

### Ingress Contract:
```json
{
  "prompt": "I prefer noir tone when writing crime fiction.",
  "role": "writers",
  "project_id": "proj_12345"
}
```

### Egress Telemetry (`PromptResponse.memory`):
```json
{
  "reply": "Drafted mystery scene adhering to craft guidelines...",
  "role": "writers",
  "agent_used": "prose_stylist",
  "trust_score": 88.5,
  "memory": {
    "enabled": true,
    "retrieval_performed": true,
    "memories_used": 2,
    "extraction_performed": true,
    "persistence_status": "success",
    "project_id": "proj_12345",
    "memories_retrieved": [
      {
        "memory_id": "mem_001",
        "memory_type": "constraint",
        "content": "Mandatory creative constraint: purple prose.",
        "relevance_score": 0.88,
        "retrieval_reason": "Score 0.88 (proj=1.0, disc=1.0, rel=0.6, imp=0.9, rec=1.0)"
      }
    ],
    "error_message": null
  }
}
```
