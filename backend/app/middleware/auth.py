from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.logging import get_logger

logger = get_logger("auth")


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        auth_header = request.headers.get("Authorization")

        # E2-S2: decode and verify Cognito JWT here, extract sub as user_id
        if not auth_header or not auth_header.startswith("Bearer "):
            logger.warning(
                "missing_or_malformed_auth_header",
                method=request.method,
                path=request.url.path,
            )

        request.state.user_id = None
        return await call_next(request)
