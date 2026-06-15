import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        auth_header = request.headers.get("Authorization")

        # E2-S2: decode and verify Cognito JWT here, extract sub as user_id
        if not auth_header or not auth_header.startswith("Bearer "):
            logger.warning(
                "Request missing or malformed Authorization header: %s %s",
                request.method,
                request.url.path,
            )

        request.state.user_id = None
        return await call_next(request)
