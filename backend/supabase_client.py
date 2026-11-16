"""
OCTS AI - Supabase Cloud Database Client & Persistence Manager
Provides unified access to Supabase PostgreSQL and PostgREST API for:
1. Creative memory records and craft constraints.
2. Projects and domain taxonomies.
3. Observability telemetry and execution events.

Gracefully degrades to local SQLite if Supabase is unconfigured or unreachable.
"""

from datetime import datetime, timezone
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger("octs.supabase")

_supabase_client = None
_client_initialized = False


def get_supabase_config() -> Dict[str, Optional[str]]:
    """Retrieves Supabase connection credentials from environment or application config."""
    url = (
        os.getenv("SUPABASE_URL")
        or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    )
    key = (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        or os.getenv("SUPABASE_KEY")
        or os.getenv("SUPABASE_ANON_KEY")
        or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
    )
    db_url = os.getenv("SUPABASE_DB_URL") or os.getenv("DATABASE_URL")
    return {
        "url": url.strip() if url else None,
        "key": key.strip() if key else None,
        "db_url": db_url.strip() if db_url else None,
    }


def is_supabase_configured() -> bool:
    """Returns True if Supabase REST API or PostgreSQL database credentials are present."""
    cfg = get_supabase_config()
    has_rest = bool(cfg["url"] and cfg["key"])
    has_db = bool(cfg["db_url"])
    return has_rest or has_db


def get_supabase_client():
    """
    Returns a thread-safe singleton Supabase client instance.
    Returns None if credentials are not configured or client library fails to initialize.
    """
    global _supabase_client, _client_initialized
    if _client_initialized:
        return _supabase_client

    cfg = get_supabase_config()
    url, key = cfg["url"], cfg["key"]

    if not url or not key:
        logger.debug("Supabase client not initialized: SUPABASE_URL or SUPABASE_KEY not configured.")
        _client_initialized = True
        _supabase_client = None
        return None

    try:
        from supabase import Client, create_client
        _supabase_client = create_client(url, key)
        _client_initialized = True
        logger.info(f"Supabase client initialized successfully for '{url}'.")
        return _supabase_client
    except Exception as e:
        logger.warning(f"Failed to create Supabase client: {e}", exc_info=True)
        _client_initialized = True
        _supabase_client = None
        return None


def reset_supabase_client() -> None:
    """Resets the singleton client to force re-initialization (e.g. after config change)."""
    global _supabase_client, _client_initialized
    _supabase_client = None
    _client_initialized = False


def test_supabase_connection() -> Dict[str, Any]:
    """
    Executes a live ping to verify Supabase connectivity and table presence.
    Returns operational metadata, latency, and available tables.
    """
    cfg = get_supabase_config()
    configured = is_supabase_configured()

    if not configured:
        return {
            "status": "not_configured",
            "message": "Supabase credentials (SUPABASE_URL and SUPABASE_KEY) are not set.",
            "mode": "sqlite_fallback",
            "latency_ms": None,
            "tables": {},
        }

    client = get_supabase_client()
    if not client:
        return {
            "status": "client_error",
            "message": "Supabase client could not be created from configured credentials.",
            "mode": "sqlite_fallback",
            "latency_ms": None,
            "tables": {},
        }

    start_time = time.perf_counter()
    table_status = {}

    try:
        # Check projects table
        try:
            p_res = client.table("projects").select("project_id").limit(1).execute()
            table_status["projects"] = "available"
        except Exception as e:
            table_status["projects"] = f"unreachable: {str(e)[:80]}"

        # Check memory_records table
        try:
            m_res = client.table("memory_records").select("memory_id").limit(1).execute()
            table_status["memory_records"] = "available"
        except Exception as e:
            table_status["memory_records"] = f"unreachable: {str(e)[:80]}"

        # Check request_telemetry table
        try:
            t_res = client.table("request_telemetry").select("request_id").limit(1).execute()
            table_status["request_telemetry"] = "available"
        except Exception as e:
            table_status["request_telemetry"] = f"unreachable: {str(e)[:80]}"

        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        any_success = any(v == "available" for v in table_status.values())

        return {
            "status": "connected" if any_success else "tables_missing",
            "message": "Connected to Supabase Cloud Database" if any_success else "Connected to Supabase, but schema tables are not yet created.",
            "url": cfg["url"],
            "mode": "supabase_cloud",
            "latency_ms": latency_ms,
            "tables": table_status,
        }
    except Exception as e:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return {
            "status": "error",
            "message": f"Connection error: {str(e)}",
            "mode": "sqlite_fallback",
            "latency_ms": latency_ms,
            "tables": table_status,
        }


# ============================================================================
# Cloud Database Sync Operations (Non-blocking & Non-fatal)
# ============================================================================

def sync_memory_record(record_dict: Dict[str, Any]) -> bool:
    """Upserts a memory record into the Supabase 'memory_records' table."""
    client = get_supabase_client()
    if not client:
        return False

    try:
        # Prepare sanitized dictionary for Postgres insertion
        row = {
            "memory_id": record_dict.get("memory_id"),
            "owner_id": record_dict.get("owner_id", "default_user"),
            "memory_type": record_dict.get("memory_type", "craft_rule"),
            "scope": record_dict.get("scope", "global"),
            "discipline": record_dict.get("discipline"),
            "project_id": record_dict.get("project_id"),
            "session_id": record_dict.get("session_id"),
            "content": record_dict.get("content", ""),
            "structured_data_json": json.dumps(record_dict.get("structured_data", {})),
            "source": record_dict.get("source", "user_explicit"),
            "confidence": float(record_dict.get("confidence", 1.0)),
            "importance": float(record_dict.get("importance", 0.7)),
            "created_at": record_dict.get("created_at", datetime.now(timezone.utc).isoformat()),
            "updated_at": record_dict.get("updated_at", datetime.now(timezone.utc).isoformat()),
            "last_accessed_at": record_dict.get("last_accessed_at"),
            "access_count": int(record_dict.get("access_count", 0)),
            "status": record_dict.get("status", "active"),
            "version": int(record_dict.get("version", 1)),
            "superseded_by": record_dict.get("superseded_by"),
        }

        # Convert datetimes to ISO string if needed
        for dt_field in ["created_at", "updated_at", "last_accessed_at"]:
            if isinstance(row[dt_field], datetime):
                row[dt_field] = row[dt_field].isoformat()

        client.table("memory_records").upsert(row, on_conflict="memory_id").execute()
        logger.debug(f"Synced memory record '{row['memory_id']}' to Supabase.")
        return True
    except Exception as e:
        logger.warning(f"Failed to sync memory '{record_dict.get('memory_id')}' to Supabase: {e}")
        return False


def delete_memory_record(memory_id: str) -> bool:
    """Deletes or marks inactive a memory record in Supabase."""
    client = get_supabase_client()
    if not client:
        return False

    try:
        client.table("memory_records").delete().eq("memory_id", memory_id).execute()
        logger.debug(f"Deleted memory '{memory_id}' from Supabase.")
        return True
    except Exception as e:
        logger.warning(f"Failed to delete memory '{memory_id}' in Supabase: {e}")
        return False


def sync_project_record(project_dict: Dict[str, Any]) -> bool:
    """Upserts a project record into the Supabase 'projects' table."""
    client = get_supabase_client()
    if not client:
        return False

    try:
        row = {
            "project_id": project_dict.get("project_id"),
            "owner_id": project_dict.get("owner_id", "default_user"),
            "name": project_dict.get("name", "Untitled Project"),
            "description": project_dict.get("description", ""),
            "discipline": project_dict.get("discipline"),
            "metadata_json": json.dumps(project_dict.get("metadata", {})),
            "is_active": bool(project_dict.get("is_active", True)),
            "created_at": project_dict.get("created_at", datetime.now(timezone.utc).isoformat()),
            "updated_at": project_dict.get("updated_at", datetime.now(timezone.utc).isoformat()),
        }

        for dt_field in ["created_at", "updated_at"]:
            if isinstance(row[dt_field], datetime):
                row[dt_field] = row[dt_field].isoformat()

        client.table("projects").upsert(row, on_conflict="project_id").execute()
        logger.debug(f"Synced project '{row['project_id']}' to Supabase.")
        return True
    except Exception as e:
        logger.warning(f"Failed to sync project '{project_dict.get('project_id')}' to Supabase: {e}")
        return False


def delete_project_record(project_id: str) -> bool:
    """Deletes a project record from Supabase."""
    client = get_supabase_client()
    if not client:
        return False

    try:
        client.table("projects").delete().eq("project_id", project_id).execute()
        logger.debug(f"Deleted project '{project_id}' from Supabase.")
        return True
    except Exception as e:
        logger.warning(f"Failed to delete project '{project_id}' in Supabase: {e}")
        return False


def sync_telemetry_record(telemetry_dict: Dict[str, Any]) -> bool:
    """Inserts a completed request telemetry entry into Supabase."""
    client = get_supabase_client()
    if not client:
        return False

    try:
        ts = telemetry_dict.get("timestamp")
        if isinstance(ts, datetime):
            ts = ts.isoformat()

        row = {
            "request_id": telemetry_dict.get("request_id"),
            "timestamp": ts or datetime.now(timezone.utc).isoformat(),
            "duration_ms": float(telemetry_dict.get("duration_ms", 0.0)),
            "status": telemetry_dict.get("status", "success"),
            "discipline": telemetry_dict.get("discipline"),
            "persona_id": telemetry_dict.get("persona_id"),
            "model_name": telemetry_dict.get("model_name"),
            "quality_score": float(telemetry_dict["quality_score"]) if telemetry_dict.get("quality_score") is not None else None,
            "reliability_score": float(telemetry_dict["reliability_score"]) if telemetry_dict.get("reliability_score") is not None else None,
            "trust_score": float(telemetry_dict["trust_score"]) if telemetry_dict.get("trust_score") is not None else None,
            "refinement_triggered": bool(telemetry_dict.get("refinement_triggered", False)),
            "recovery_attempts": int(telemetry_dict.get("recovery_attempts", 0)),
            "reverted_to_baseline": bool(telemetry_dict.get("reverted_to_baseline", False)),
            "memory_injected": bool(telemetry_dict.get("memory_injected", False)),
            "memory_count": int(telemetry_dict.get("memory_count", 0)),
            "error_type": telemetry_dict.get("error_type"),
            "error_message": telemetry_dict.get("error_message"),
            "client_ip": telemetry_dict.get("client_ip"),
            "user_agent": telemetry_dict.get("user_agent"),
            "metadata_json": json.dumps(telemetry_dict.get("metadata", {})),
        }

        client.table("request_telemetry").insert(row).execute()
        return True
    except Exception as e:
        logger.debug(f"Telemetry sync to Supabase skipped or failed: {e}")
        return False


def sync_execution_event(event_dict: Dict[str, Any]) -> bool:
    """Inserts an execution event entry into Supabase."""
    client = get_supabase_client()
    if not client:
        return False

    try:
        ts = event_dict.get("timestamp")
        if isinstance(ts, datetime):
            ts = ts.isoformat()

        row = {
            "event_id": event_dict.get("event_id"),
            "request_id": event_dict.get("request_id"),
            "timestamp": ts or datetime.now(timezone.utc).isoformat(),
            "event_type": event_dict.get("event_type", "unknown"),
            "component": event_dict.get("component", "system"),
            "duration_ms": float(event_dict["duration_ms"]) if event_dict.get("duration_ms") is not None else None,
            "payload_json": json.dumps(event_dict.get("payload", {})),
        }

        client.table("execution_events").insert(row).execute()
        return True
    except Exception as e:
        logger.debug(f"Event sync to Supabase skipped or failed: {e}")
        return False
