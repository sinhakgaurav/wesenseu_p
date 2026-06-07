"""HTTP request/response logging middleware."""
from __future__ import annotations

import logging
import time
import uuid
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("monitour.http")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
        start = time.perf_counter()
        path = request.url.path
        method = request.method

        logger.info("→ %s %s [%s]", method, path, request_id)
        try:
            response = await call_next(request)
        except Exception:
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.exception("✗ %s %s [%s] %.0fms — unhandled error", method, path, request_id, elapsed_ms)
            raise

        elapsed_ms = (time.perf_counter() - start) * 1000
        level = logging.WARNING if response.status_code >= 400 else logging.INFO
        logger.log(
            level,
            "← %s %s [%s] %s %.0fms",
            method,
            path,
            request_id,
            response.status_code,
            elapsed_ms,
        )
        response.headers["X-Request-ID"] = request_id
        return response
