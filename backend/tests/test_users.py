from fastapi.testclient import TestClient

from app.services.users import create as create_user
from tests.conftest import make_token


def _seed_user(
    sub: str = "user-sub-123",
    email: str = "test@example.com",
) -> None:
    create_user(sub, email)


class TestPatchMe:
    def test_valid_update_returns_200_with_updated_name(self, client: TestClient):
        _seed_user()
        token = make_token()
        resp = client.patch(
            "/api/users/me",
            json={"display_name": "CoolPlayer99"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["display_name"] == "CoolPlayer99"

    def test_strips_surrounding_whitespace(self, client: TestClient):
        _seed_user()
        token = make_token()
        resp = client.patch(
            "/api/users/me",
            json={"display_name": "  TrimMe  "},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["display_name"] == "TrimMe"

    def test_empty_string_returns_422(self, client: TestClient):
        _seed_user()
        token = make_token()
        resp = client.patch(
            "/api/users/me",
            json={"display_name": ""},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

    def test_too_short_returns_422(self, client: TestClient):
        _seed_user()
        token = make_token()
        resp = client.patch(
            "/api/users/me",
            json={"display_name": "ab"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

    def test_too_long_returns_422(self, client: TestClient):
        _seed_user()
        token = make_token()
        resp = client.patch(
            "/api/users/me",
            json={"display_name": "A" * 31},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

    def test_special_chars_returns_422(self, client: TestClient):
        _seed_user()
        token = make_token()
        resp = client.patch(
            "/api/users/me",
            json={"display_name": "Bad!Name@"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

    def test_missing_auth_returns_401(self, client: TestClient):
        resp = client.patch(
            "/api/users/me",
            json={"display_name": "ValidName"},
        )
        assert resp.status_code == 401
