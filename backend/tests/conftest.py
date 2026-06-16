import os
import time

import boto3
import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from moto import mock_aws

from app.auth.verifier import CognitoJwtVerifier, get_verifier
from app.config import settings
from app.main import app
from app.services.users import reset_seen_cache

# Keep boto3 fully offline during tests: dummy credentials so botocore never
# walks its chain out to the EC2 metadata service (which hangs off-AWS), and an
# explicit IMDS disable for good measure. moto ignores the credential values.
os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")
os.environ.setdefault("AWS_SESSION_TOKEN", "testing")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
os.environ.setdefault("AWS_EC2_METADATA_DISABLED", "true")

# ---------------------------------------------------------------------------
# RSA keypair — generated once for the entire test session
# ---------------------------------------------------------------------------
_PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_PUBLIC_KEY = _PRIVATE_KEY.public_key()

_PUBLIC_KEY_PEM = _PUBLIC_KEY.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo,
)

TEST_KID = "test-key-id-1"
TEST_ISS = "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_TEST"
TEST_AUD = "test-app-client-id"


# ---------------------------------------------------------------------------
# Token factory
# ---------------------------------------------------------------------------
def make_token(**overrides) -> str:
    """Sign a minimal Cognito ID token with the test private key.

    Any key in overrides replaces the corresponding default claim, allowing
    tests to inject expired timestamps, wrong audiences, wrong token_use, etc.
    """
    now = int(time.time())
    defaults: dict = {
        "iss": TEST_ISS,
        "aud": TEST_AUD,
        "sub": "user-sub-123",
        "email": "test@example.com",
        "token_use": "id",
        "exp": now + 3600,
    }
    payload = {**defaults, **overrides}
    headers = {"kid": TEST_KID}
    return jwt.encode(payload, _PRIVATE_KEY, algorithm="RS256", headers=headers)


# ---------------------------------------------------------------------------
# Fake JWK client — returns the test public key without any network call
# ---------------------------------------------------------------------------
class _FakeSigningKey:
    key = _PUBLIC_KEY_PEM


class _FakeJwkClient:
    def get_signing_key_from_jwt(self, token: str):  # noqa: ARG002
        return _FakeSigningKey()


_FAKE_JWK_CLIENT = _FakeJwkClient()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def clear_seen_cache():
    """Isolate the in-process user cache between tests."""
    reset_seen_cache()
    yield
    reset_seen_cache()


@pytest.fixture()
def mock_dynamo(monkeypatch):
    """Spin up a moto DynamoDB mock and create the Users table."""
    monkeypatch.setattr(settings, "USERS_TABLE", "mundial-users-test")
    monkeypatch.setattr(settings, "JWT_ISSUER", TEST_ISS)
    monkeypatch.setattr(settings, "COGNITO_APP_CLIENT_ID", TEST_AUD)
    # Force the app's boto3 resource onto moto's mocked backend instead of the
    # dynamodb-local endpoint that .env injects into settings.
    monkeypatch.setattr(settings, "DYNAMODB_ENDPOINT_URL", None)

    # moto mock_aws must wrap the table creation AND the code under test.
    with mock_aws():
        # Reset any cached boto3 resource so moto intercepts the connection.
        import app.db.dynamo as _dynamo_module

        _dynamo_module._resource = None

        boto3.resource("dynamodb", region_name="us-east-1").create_table(
            TableName="mundial-users-test",
            KeySchema=[{"AttributeName": "user_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "user_id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        yield

    # Restore the dynamo resource so subsequent tests start clean.
    _dynamo_module._resource = None


@pytest.fixture()
def override_verifier():
    """Replace the real CognitoJwtVerifier with a test instance backed by the fake JWK client."""
    test_verifier = CognitoJwtVerifier(
        issuer=TEST_ISS,
        audience=TEST_AUD,
        jwk_client=_FAKE_JWK_CLIENT,
    )
    app.dependency_overrides[get_verifier] = lambda: test_verifier
    yield test_verifier
    app.dependency_overrides.clear()


@pytest.fixture()
def client(mock_dynamo, override_verifier):
    """TestClient with moto DynamoDB and the fake verifier wired in."""
    return TestClient(app)
