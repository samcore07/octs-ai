"""
OCTS AI - Request Correlation & Error Boundary Middleware
Starlette/FastAPI middleware managing request IDs, response headers, and global exception safety.
"""

import logging
import time
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from backend.observability.context import clear_request_context, set_request_context
from backend.observability.correlation import resolve_request_id
from backend.observability.error_tracking import build_safe_error_response

logger = logging.getLogger("octs.observability.middleware")


class RequestCorrelationMiddleware(BaseHTTPMiddleware):
    """
    Ensures every HTTP request is tagged with a correlated request ID,
    propagated through contextvars, returned in response headers,
    and wrapped in a safe error boundary.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 1. Resolve or generate request ID
        req_id = resolve_request_id(dict(request.headers))
        set_request_context(request_id=req_id, correlation_id=req_id)

        start_time = time.perf_counter()

        try:
            response = await call_next(request)
            # Attach correlation ID to response headers
            response.headers["X-Request-ID"] = req_id
            return response
        except Exception as exc:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            logger.error(
                f"Unhandled exception in HTTP pipeline [req_id={req_id}, dur={duration_ms}ms]: {exc}",
                exc_info=True,
            )

            # Build safe response without stack trace leakage
            safe_payload = build_safe_error_response(exc, request_id=req_id)
            status_code = safe_payload.get("status_code", 500)

            err_response = JSONResponse(
                content=safe_payload,
                status_code=status_code,
            )
            err_response.headers["X-Request-ID"] = req_id
            return err_response
        finally:
            clear_request_context()
