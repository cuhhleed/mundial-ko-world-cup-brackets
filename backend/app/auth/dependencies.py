from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.verifier import GoogleJwtVerifier, InvalidTokenError, get_verifier
from app.logging import get_logger
from app.models.user import AuthenticatedUser

logger = get_logger("auth")

_bearer = HTTPBearer(auto_error=False)

# Future E4: add an `optional_user` dependency that returns AuthenticatedUser | None
# without raising a 401 for unauthenticated requests (used on public endpoints that
# want to personalize the response when a user happens to be logged in).


def require_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    verifier: GoogleJwtVerifier = Depends(get_verifier),
) -> AuthenticatedUser:
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        claims = verifier.verify(credentials.credentials)
    except InvalidTokenError:
        logger.warning("invalid_token_rejected")
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # AuthConfigError and any unexpected exception intentionally propagate → 500.

    user = AuthenticatedUser(user_id=claims["sub"], email=claims["email"])
    request.state.user = user
    return user
