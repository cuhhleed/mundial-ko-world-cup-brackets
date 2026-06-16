from functools import lru_cache

from jwt import PyJWKClient, PyJWTError, decode

from app.config import settings
from app.logging import get_logger

logger = get_logger("verifier")


class InvalidTokenError(Exception):
    """Any bearer token that fails verification — maps to a 401 upstream."""


class AuthConfigError(Exception):
    """For invalid or missing auth components."""


class CognitoJwtVerifier:
    def __init__(self, issuer, audience, *, jwk_client=None):
        # fail fast: issuer/audience are None-defaulted in config — a missing one
        # is a deploy misconfig, not a request error. Raise here, not in verify().
        if (not issuer) or (not audience):
            err_msg = "Missing issuer or audience during verification."
            logger.error("missing_auth_verification", error=err_msg)
            raise AuthConfigError(err_msg)
        # The seam (see below): default to a real PyJWKClient, but ALLOW one to be
        # passed in so tests can swap the network fetch for a local key.
        self.issuer = issuer
        self.audience = audience
        self._jwk_client = jwk_client or PyJWKClient(
            f"{issuer}/.well-known/jwks.json", cache_keys=True
        )

    def verify(self, token: str) -> dict:
        try:
            signing_key = self._jwk_client.get_signing_key_from_jwt(token)
            claims = decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self.audience,        # ID token aud == app client id
                issuer=self.issuer,
                options={"require": ["exp", "iss", "sub", "aud", "email"]},
            )
        except PyJWTError as e:
            raise InvalidTokenError(str(e)) from e

        if claims.get("token_use") != "id":  # reject access tokens
            raise InvalidTokenError("expected an ID token")
        return claims


@lru_cache
def get_verifier() -> CognitoJwtVerifier:
    return CognitoJwtVerifier(settings.JWT_ISSUER, settings.COGNITO_APP_CLIENT_ID)
