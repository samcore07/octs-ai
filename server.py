"""
Octs AI - Application Entrypoint & Gateway Server
Modularized FastAPI implementation with LangSmith tracing and configurable CORS.
"""

import logging
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from langchain.chat_models import init_chat_model

from backend.config import get_settings
from backend.schemas import HealthResponse, PromptRequest, PromptResponse
from backend.tracing import setup_tracing
from backend.agents.routing import AgentRouter
from backend.orchestration import OrchestrationExecutor

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
model = init_chat_model(
    settings.model_name,
    model_provider=settings.model_provider,
    temperature=settings.model_temperature,
    api_key=settings.gemini_api_key,
)

# Initialize Agent Persona Router & Orchestration Executor with Injected Dependencies
router = AgentRouter()
executor = OrchestrationExecutor(model=model, router=router)


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
def ask_gemini(request: PromptRequest):
    """
    Primary execution endpoint.
    Maintains exact backward compatibility with frontend: returns {'reply': ...}
    """
    logger.info(f"Received prompt: {request.prompt[:80]}... (length={len(request.prompt)})")
    start_time = performance_time = time.perf_counter()

    try:
        active_executor = executor
        if active_executor.model is not model:
            active_executor = OrchestrationExecutor(model=model, router=router)

        response = active_executor.execute_prompt(
            prompt=request.prompt,
            role=request.role,
            session_id=request.session_id,
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


# 5. Serve static files (HTML, CSS, JS, pages/)
app.mount("/", StaticFiles(directory="."), name="static")
