import os
import time

import boto3
import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from moto import mock_aws

from app.auth.verifier import GoogleJwtVerifier, get_verifier
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
TEST_ISS = "https://accounts.google.com"
TEST_AUD = "test-google-client-id"


# ---------------------------------------------------------------------------
# Token factory
# ---------------------------------------------------------------------------
def make_token(**overrides) -> str:
    """Sign a minimal Google ID token with the test private key.

    Any key in overrides replaces the corresponding default claim, allowing
    tests to inject expired timestamps, wrong audiences, wrong issuers, etc.
    """
    now = int(time.time())
    defaults: dict = {
        "iss": TEST_ISS,
        "aud": TEST_AUD,
        "sub": "user-sub-123",
        "email": "test@example.com",
        "email_verified": True,
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
    """Spin up a moto DynamoDB mock and create the Users, Brackets, and Matches tables."""
    monkeypatch.setattr(settings, "USERS_TABLE", "mundial-users-test")
    monkeypatch.setattr(settings, "BRACKETS_TABLE", "mundial-brackets-test")
    monkeypatch.setattr(settings, "MATCHES_TABLE", "mundial-matches-test")
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", TEST_AUD)
    # Force the app's boto3 resource onto moto's mocked backend instead of the
    # dynamodb-local endpoint that .env injects into settings.
    monkeypatch.setattr(settings, "DYNAMODB_ENDPOINT_URL", None)

    # moto mock_aws must wrap the table creation AND the code under test.
    with mock_aws():
        # Reset any cached boto3 resource so moto intercepts the connection.
        import app.db.dynamo as _dynamo_module

        _dynamo_module._resource = None

        dynamo = boto3.resource("dynamodb", region_name="us-east-1")

        dynamo.create_table(
            TableName="mundial-users-test",
            KeySchema=[{"AttributeName": "user_id", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "user_id", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        dynamo.create_table(
            TableName="mundial-brackets-test",
            KeySchema=[{"AttributeName": "bracket_id", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "bracket_id", "AttributeType": "S"},
                {"AttributeName": "user_id", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[{
                "IndexName": "user_id-index",
                "KeySchema": [{"AttributeName": "user_id", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            }],
            BillingMode="PAY_PER_REQUEST",
        )

        dynamo.create_table(
            TableName="mundial-matches-test",
            KeySchema=[{"AttributeName": "match_id", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "match_id", "AttributeType": "S"},
                {"AttributeName": "round", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[{
                "IndexName": "round-index",
                "KeySchema": [{"AttributeName": "round", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            }],
            BillingMode="PAY_PER_REQUEST",
        )

        yield

    # Restore the dynamo resource so subsequent tests start clean.
    _dynamo_module._resource = None


@pytest.fixture()
def override_verifier():
    """Replace the real GoogleJwtVerifier with a test instance backed by the fake JWK client."""
    test_verifier = GoogleJwtVerifier(
        audience=TEST_AUD,
        issuers=[TEST_ISS],
        jwk_client=_FAKE_JWK_CLIENT,
    )
    app.dependency_overrides[get_verifier] = lambda: test_verifier
    yield test_verifier
    app.dependency_overrides.clear()


@pytest.fixture()
def client(mock_dynamo, override_verifier):
    """TestClient with moto DynamoDB and the fake verifier wired in."""
    return TestClient(app)
