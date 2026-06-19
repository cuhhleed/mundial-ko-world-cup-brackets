from functools import lru_cache

from jwt import PyJWKClient, PyJWTError, decode

from app.config import settings
from app.logging import get_logger

logger = get_logger("verifier")

GOOGLE_ISSUERS = ["https://accounts.google.com", "accounts.google.com"]
GOOGLE_JWKS_URI = "https://www.googleapis.com/oauth2/v3/certs"


class InvalidTokenError(Exception):
    """Any bearer token that fails verification — maps to a 401 upstream."""


class AuthConfigError(Exception):
    """For invalid or missing auth components."""


class GoogleJwtVerifier:
    def __init__(
        self,
        audience,
        *,
        issuers=GOOGLE_ISSUERS,
        jwks_uri=GOOGLE_JWKS_URI,
        jwk_client=None,
    ):
        # fail fast: audience is None-defaulted in config — a missing one
        # is a deploy misconfig, not a request error. Raise here, not in verify().
        if not audience:
            err_msg = "Missing audience during verification."
            logger.error("missing_auth_verification", error=err_msg)
            raise AuthConfigError(err_msg)
        self.audience = audience
        self.issuers = issuers
        # The seam: default to a real PyJWKClient, but ALLOW one to be
        # passed in so tests can swap the network fetch for a local key.
        self._jwk_client = jwk_client or PyJWKClient(jwks_uri, cache_keys=True)

    def verify(self, token: str) -> dict:
        try:
            signing_key = self._jwk_client.get_signing_key_from_jwt(token)
            claims = decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self.audience,
                issuer=self.issuers,  # PyJWT accepts a list of acceptable issuers
                options={"require": ["exp", "iss", "sub", "aud", "email"]},
            )
        except PyJWTError as e:
            raise InvalidTokenError(str(e)) from e

        # Reject unverified email accounts
        if claims.get("email_verified") is not True:
            raise InvalidTokenError("email not verified")

        return claims


@lru_cache
def get_verifier() -> GoogleJwtVerifier:
    return GoogleJwtVerifier(settings.GOOGLE_CLIENT_ID)
