"""
Octs AI - Application Entrypoint & Gateway Server
Modularized FastAPI implementation with LangSmith tracing and configurable CORS.
"""

import logging
import time
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from langchain.chat_models import init_chat_model

from backend.config import get_settings
from backend.schemas import HealthResponse, PromptRequest, PromptResponse
from backend.tracing import setup_tracing
from backend.agents.routing import AgentRouter
from backend.orchestration import OrchestrationExecutor
from backend.memory import (
    MemoryCreate,
    MemoryManager,
    MemoryRecord,
    MemoryStatus,
    MemoryType,
    MemoryUpdate,
    ProjectCreate,
    ProjectRecord,
    ProjectUpdate,
)

# Configure application logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("octs.server")
logging.getLogger("google_genai").setLevel(logging.ERROR)

# Load validated configuration
settings = get_settings()

# Initialize optional LangSmith observability (fails gracefully if unconfigured)
setup_tracing(settings)

# Ensure Gemini API key is configured before booting model
if not settings.gemini_api_key:
    logger.error("GEMINI_API_KEY not found in environment configuration!")
    raise RuntimeError("GEMINI_API_KEY not found in .env file or environment!")

# Export for underlying google genai SDK
import os
os.environ["GEMINI_API_KEY"] = settings.gemini_api_key
os.environ["GOOGLE_API_KEY"] = settings.gemini_api_key

# Initialize FastAPI Gateway
app = FastAPI(
    title="Octs AI - Creative Harness Gateway",
    version="0.2.0",
    description="Enterprise multi-agent creative execution harness.",
)

# Configure CORS with strict, configurable origins (replacing wildcard)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Initialize Primary LLM
model_init_kwargs = {
    "model_provider": settings.model_provider,
    "api_key": settings.gemini_api_key,
}
if "flash-lite" not in settings.model_name.lower():
    model_init_kwargs["temperature"] = settings.model_temperature

model = init_chat_model(
    settings.model_name,
    **model_init_kwargs,
)

# Initialize Agent Persona Router, Memory Manager & Orchestration Executor with Injected Dependencies
router = AgentRouter()
memory_manager = MemoryManager()
executor = OrchestrationExecutor(model=model, router=router, memory_manager=memory_manager)


# 1. Health & Diagnostics Endpoint
@app.get("/api/health", response_model=HealthResponse)
def health_check():
    """System health inspection endpoint."""
    return HealthResponse(
        status="ok",
        version="0.2.0",
        model_provider=settings.model_provider,
        model_name=settings.model_name,
        langsmith_tracing=settings.is_langsmith_active(),
    )


# 2. Serve index.html when visiting root
@app.get("/")
def serve_home():
    """Serves root Dashboard application."""
    return FileResponse("index.html")


# 3. Handle prompt execution via POST /ask (Exact Backward-Compatible Interface)
@app.post("/ask", response_model=PromptResponse)
def ask_gemini(request: PromptRequest, req: Request):
    """
    Primary execution endpoint.
    Maintains exact backward compatibility with frontend: returns {'reply': ...}
    """
    logger.info(f"Received prompt: {request.prompt[:80]}... (length={len(request.prompt)})")
    start_time = performance_time = time.perf_counter()

    try:
        active_executor = executor
        if active_executor.model is not model:
            active_executor = OrchestrationExecutor(model=model, router=router, memory_manager=memory_manager)

        # Resolve caller identity via IdentityProvider abstraction
        identity = memory_manager.identity_provider.resolve_identity(
            headers=dict(req.headers),
            explicit_owner_id=request.owner_id,
        )

        response = active_executor.execute_prompt(
            prompt=request.prompt,
            role=request.role,
            session_id=request.session_id,
            task_type=request.task_type,
            project_id=request.project_id,
            owner_id=identity.owner_id,
        )
        return response
    except Exception as e:
        logger.error(f"ERROR IN /ask: {repr(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# 4. Safe fallback for accidental GET /ask requests to avoid confusing 405s
@app.get("/ask")
def ask_gemini_get_fallback():
    """Friendly guard against GET requests to the prompt execution endpoint."""
    return {
        "status": "error",
        "message": "The /ask endpoint requires an HTTP POST request with a JSON payload: {'prompt': '...'}",
    }


# ==============================================================================
# Phase 6: Memory & Project Management API Endpoints
# ==============================================================================

# Projects API Endpoints (Must be registered before /api/memory/{memory_id} to prevent path collisions)

@app.get("/api/memory/projects", response_model=List[ProjectRecord])
def list_projects(req: Request):
    """Lists active projects for the authenticated caller."""
    identity = memory_manager.identity_provider.resolve_identity(headers=dict(req.headers))
    return memory_manager.list_projects(owner_id=identity.owner_id)


@app.post("/api/memory/projects", response_model=ProjectRecord, status_code=201)
def create_project(payload: ProjectCreate, req: Request):
    """Creates a new creative project definition."""
    identity = memory_manager.identity_provider.resolve_identity(headers=dict(req.headers))
    return memory_manager.create_project(create_data=payload, owner_id=identity.owner_id)


@app.get("/api/memory/projects/{project_id}", response_model=ProjectRecord)
def get_project(project_id: str, req: Request):
    """Retrieves metadata for a specific project."""
    identity = memory_manager.identity_provider.resolve_identity(headers=dict(req.headers))
    proj = memory_manager.get_project(project_id=project_id, owner_id=identity.owner_id)
    if not proj:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")
    return proj


@app.patch("/api/memory/projects/{project_id}", response_model=ProjectRecord)
def update_project(project_id: str, payload: ProjectUpdate, req: Request):
    """Updates an existing creative project."""
    identity = memory_manager.identity_provider.resolve_identity(headers=dict(req.headers))
    updated = memory_manager.update_project(project_id=project_id, update_data=payload, owner_id=identity.owner_id)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")
    return updated


@app.delete("/api/memory/projects/{project_id}")
def delete_project(project_id: str, req: Request):
    """Deactivates a project and archives associated project-scoped memories."""
    identity = memory_manager.identity_provider.resolve_identity(headers=dict(req.headers))
    deleted = memory_manager.delete_project(project_id=project_id, owner_id=identity.owner_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")
    return {"status": "success", "message": f"Project '{project_id}' deleted."}


# Memory Records API Endpoints

@app.get("/api/memory", response_model=List[MemoryRecord])
def list_memories(
    req: Request,
    project_id: Optional[str] = None,
    discipline: Optional[str] = None,
    memory_type: Optional[str] = None,
    status: Optional[str] = "active",
    limit: int = 50,
    offset: int = 0,
):
    """Lists persistent memory records with optional category and project filtering."""
    identity = memory_manager.identity_provider.resolve_identity(headers=dict(req.headers))
    mem_type_enum = MemoryType(memory_type) if memory_type else None
    mem_status_enum = MemoryStatus(status) if status else None
    return memory_manager.list_memories(
        owner_id=identity.owner_id,
        project_id=project_id,
        discipline=discipline,
        memory_type=mem_type_enum,
        status=mem_status_enum,
        limit=limit,
        offset=offset,
    )


@app.get("/api/memory/{memory_id}", response_model=MemoryRecord)
def get_memory(memory_id: str, req: Request):
    """Retrieves a single memory record by ID."""
    identity = memory_manager.identity_provider.resolve_identity(headers=dict(req.headers))
    mem = memory_manager.get_memory(memory_id=memory_id, owner_id=identity.owner_id)
    if not mem:
        raise HTTPException(status_code=404, detail=f"Memory record '{memory_id}' not found.")
    return mem


@app.post("/api/memory", response_model=MemoryRecord, status_code=201)
def create_memory(payload: MemoryCreate, req: Request):
    """Explicitly stores a new memory record."""
    identity = memory_manager.identity_provider.resolve_identity(headers=dict(req.headers))
    return memory_manager.create_memory(create_data=payload, owner_id=identity.owner_id)


@app.patch("/api/memory/{memory_id}", response_model=MemoryRecord)
def update_memory(memory_id: str, payload: MemoryUpdate, req: Request):
    """Updates content or status of an existing memory record."""
    identity = memory_manager.identity_provider.resolve_identity(headers=dict(req.headers))
    updated = memory_manager.update_memory(memory_id=memory_id, update_data=payload, owner_id=identity.owner_id)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Memory record '{memory_id}' not found.")
    return updated


@app.delete("/api/memory/{memory_id}")
def delete_memory(memory_id: str, req: Request):
    """Soft-deletes a memory record."""
    identity = memory_manager.identity_provider.resolve_identity(headers=dict(req.headers))
    deleted = memory_manager.delete_memory(memory_id=memory_id, owner_id=identity.owner_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Memory record '{memory_id}' not found.")
    return {"status": "success", "message": f"Memory '{memory_id}' deleted."}


# 5. Serve static files (HTML, CSS, JS, pages/)
app.mount("/", StaticFiles(directory="."), name="static")
