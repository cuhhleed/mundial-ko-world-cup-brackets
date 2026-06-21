"""
Tests for the Google JWT auth dependency and /api/users/me endpoint.
"""

import re
import time

import jwt as pyjwt
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from app.auth.verifier import get_verifier
from app.config import settings
from app.db.dynamo import get_table
from app.main import app
from app.services.users import create as create_user
from tests.conftest import TEST_AUD, TEST_ISS, make_token

# Regex that matches the auto-generated display_name: two CamelCase words + 1-2 digits.
DISPLAY_NAME_RE = re.compile(r"^[A-Za-z]+[A-Za-z]+\d{1,2}$")


class TestGetMe:
    def test_valid_token_existing_user_returns_200(self, client: TestClient):
        create_user("abc-123", "player@example.com")
        token = make_token(sub="abc-123", email="player@example.com")
        resp = client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == "abc-123"
        assert data["email"] == "player@example.com"

    def test_valid_token_no_user_returns_404(self, client: TestClient):
        token = make_token(sub="no-such-user", email="nobody@example.com")
        resp = client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 404

    def test_signup_creates_dynamo_record_with_display_name(
        self, client: TestClient, mock_dynamo
    ):
        create_user("abc-123", "player@example.com")
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
        token = make_token(iss="https://evil.example.com/issuer")
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
                "email_verified": True,
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

    def test_unverified_email_returns_401(self, client: TestClient):
        """Google tokens with email_verified=false must be rejected."""
        token = make_token(email_verified=False)
        resp = client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401

    def test_accounts_google_com_issuer_accepted(self, mock_dynamo, override_verifier):
        """Both Google issuer strings must be accepted."""
        from app.auth.verifier import GoogleJwtVerifier
        from tests.conftest import _FAKE_JWK_CLIENT

        alt_verifier = GoogleJwtVerifier(
            audience=TEST_AUD,
            issuers=["accounts.google.com"],
            jwk_client=_FAKE_JWK_CLIENT,
        )
        app.dependency_overrides[get_verifier] = lambda: alt_verifier
        try:
            create_user("alt-user", "alt@example.com")
            alt_token = make_token(sub="alt-user", iss="accounts.google.com")
            alt_client = TestClient(app)
            resp = alt_client.get(
                "/api/users/me", headers={"Authorization": f"Bearer {alt_token}"}
            )
            assert resp.status_code == 200
        finally:
            app.dependency_overrides.clear()

    def test_health_without_token_returns_200(self, client: TestClient):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_get_me_returns_same_user_on_repeated_calls(
        self, client: TestClient, mock_dynamo
    ):
        create_user("idem-user", "idem@example.com")
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
