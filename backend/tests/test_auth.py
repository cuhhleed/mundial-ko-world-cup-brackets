"""
Tests for the Cognito JWT auth dependency and /api/users/me endpoint.
"""

import re
import time

import jwt as pyjwt
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from app.config import settings
from app.db.dynamo import get_table
from app.main import app
from tests.conftest import TEST_AUD, TEST_ISS, make_token

# Regex that matches the auto-generated display_name: two CamelCase words + 1-2 digits.
DISPLAY_NAME_RE = re.compile(r"^[A-Za-z]+[A-Za-z]+\d{1,2}$")


class TestGetMe:
    def test_valid_token_returns_200_with_user(self, client: TestClient):
        token = make_token(sub="abc-123", email="player@example.com")
        resp = client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == "abc-123"
        assert data["email"] == "player@example.com"

    def test_valid_token_creates_dynamo_record_with_display_name(
        self, client: TestClient, mock_dynamo
    ):
        token = make_token(sub="abc-123", email="player@example.com")
        resp = client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200

        item = get_table(settings.USERS_TABLE).get_item(Key={"user_id": "abc-123"}).get("Item")
        assert item is not None
        assert item["user_id"] == "abc-123"
        assert item["email"] == "player@example.com"
        assert DISPLAY_NAME_RE.match(item["display_name"]), (
            f"display_name {item['display_name']!r} did not match expected pattern"
        )

    def test_missing_authorization_returns_401(self, client: TestClient):
        resp = client.get("/api/users/me")
        assert resp.status_code == 401

    def test_non_bearer_scheme_returns_401(self, client: TestClient):
        token = make_token()
        resp = client.get("/api/users/me", headers={"Authorization": f"Basic {token}"})
        assert resp.status_code == 401

    def test_expired_token_returns_401(self, client: TestClient):
        expired_token = make_token(exp=int(time.time()) - 10)
        resp = client.get(
            "/api/users/me", headers={"Authorization": f"Bearer {expired_token}"}
        )
        assert resp.status_code == 401

    def test_wrong_audience_returns_401(self, client: TestClient):
        token = make_token(aud="wrong-client-id")
        resp = client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401

    def test_wrong_issuer_returns_401(self, client: TestClient):
        token = make_token(iss="https://evil.example.com/pool")
        resp = client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401

    def test_signature_by_different_key_returns_401(
        self, mock_dynamo, override_verifier
    ):
        """Token signed by a key unknown to the fake JWK client is rejected."""
        other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        token = pyjwt.encode(
            {
                "iss": TEST_ISS,
                "aud": TEST_AUD,
                "sub": "sub-x",
                "email": "x@example.com",
                "token_use": "id",
                "exp": int(time.time()) + 3600,
            },
            other_key,
            algorithm="RS256",
            headers={"kid": "test-key-id-1"},
        )
        # Use the module-level app (override_verifier fixture already patched it).
        bad_client = TestClient(app)
        resp = bad_client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401

    def test_access_token_use_returns_401(self, client: TestClient):
        token = make_token(token_use="access")
        resp = client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401

    def test_health_without_token_returns_200(self, client: TestClient):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_idempotency_two_requests_create_one_record(
        self, client: TestClient, mock_dynamo
    ):
        token = make_token(sub="idem-user", email="idem@example.com")
        headers = {"Authorization": f"Bearer {token}"}

        resp1 = client.get("/api/users/me", headers=headers)
        resp2 = client.get("/api/users/me", headers=headers)

        assert resp1.status_code == 200
        assert resp2.status_code == 200

        # Verify only one record in the table.
        table = get_table(settings.USERS_TABLE)
        scan = table.scan(
            FilterExpression="user_id = :uid",
            ExpressionAttributeValues={":uid": "idem-user"},
        )
        assert scan["Count"] == 1
