from fastapi.testclient import TestClient

from app.services.users import create as create_user
from tests.conftest import make_token

# ---------------------------------------------------------------------------
# GET /api/leaderboard
# ---------------------------------------------------------------------------


class TestGetLeaderboard:
    def test_leaderboard_returns_entries(self, client: TestClient, monkeypatch):
        u1 = create_user("uid-1", "u1@test.com")
        u2 = create_user("uid-2", "u2@test.com")
        u3 = create_user("uid-3", "u3@test.com")

        async def mock_get_top(limit):
            return [("uid-1", 100.0), ("uid-2", 80.0), ("uid-3", 60.0)]

        async def mock_get_count():
            return 3

        monkeypatch.setattr("app.db.cache.get_leaderboard_top", mock_get_top)
        monkeypatch.setattr("app.db.cache.get_leaderboard_count", mock_get_count)

        resp = client.get("/api/leaderboard")

        assert resp.status_code == 200
        body = resp.json()
        assert body["total_participants"] == 3
        entries = body["entries"]
        assert len(entries) == 3

        assert entries[0]["rank"] == 1
        assert entries[0]["display_name"] == u1.display_name
        assert entries[0]["total_points"] == 100

        assert entries[1]["rank"] == 2
        assert entries[1]["display_name"] == u2.display_name
        assert entries[1]["total_points"] == 80

        assert entries[2]["rank"] == 3
        assert entries[2]["display_name"] == u3.display_name
        assert entries[2]["total_points"] == 60

    def test_leaderboard_respects_limit(self, client: TestClient, monkeypatch):
        create_user("uid-1", "u1@test.com")
        create_user("uid-2", "u2@test.com")

        async def mock_get_top(limit):
            all_entries = [("uid-1", 100.0), ("uid-2", 80.0), ("uid-3", 60.0)]
            return all_entries[:limit]

        async def mock_get_count():
            return 3

        monkeypatch.setattr("app.db.cache.get_leaderboard_top", mock_get_top)
        monkeypatch.setattr("app.db.cache.get_leaderboard_count", mock_get_count)

        resp = client.get("/api/leaderboard?limit=2")

        assert resp.status_code == 200
        body = resp.json()
        assert len(body["entries"]) == 2

    def test_leaderboard_empty(self, client: TestClient, monkeypatch):
        async def mock_get_top(limit):
            return []

        async def mock_get_count():
            return 0

        monkeypatch.setattr("app.db.cache.get_leaderboard_top", mock_get_top)
        monkeypatch.setattr("app.db.cache.get_leaderboard_count", mock_get_count)

        resp = client.get("/api/leaderboard")

        assert resp.status_code == 200
        body = resp.json()
        assert body["entries"] == []
        assert body["total_participants"] == 0

    def test_leaderboard_no_auth_required(self, client: TestClient, monkeypatch):
        async def mock_get_top(limit):
            return []

        async def mock_get_count():
            return 0

        monkeypatch.setattr("app.db.cache.get_leaderboard_top", mock_get_top)
        monkeypatch.setattr("app.db.cache.get_leaderboard_count", mock_get_count)

        resp = client.get("/api/leaderboard")

        assert resp.status_code == 200

    def test_leaderboard_limit_validation(self, client: TestClient, monkeypatch):
        async def mock_get_top(limit):
            return []

        async def mock_get_count():
            return 0

        monkeypatch.setattr("app.db.cache.get_leaderboard_top", mock_get_top)
        monkeypatch.setattr("app.db.cache.get_leaderboard_count", mock_get_count)

        assert client.get("/api/leaderboard?limit=0").status_code == 422
        assert client.get("/api/leaderboard?limit=201").status_code == 422

    def test_leaderboard_missing_user_shows_unknown(
        self, client: TestClient, monkeypatch
    ):
        create_user("uid-known", "known@test.com")

        async def mock_get_top(limit):
            return [("uid-known", 50.0), ("uid-ghost", 30.0)]

        async def mock_get_count():
            return 2

        monkeypatch.setattr("app.db.cache.get_leaderboard_top", mock_get_top)
        monkeypatch.setattr("app.db.cache.get_leaderboard_count", mock_get_count)

        resp = client.get("/api/leaderboard")

        assert resp.status_code == 200
        entries = resp.json()["entries"]
        assert entries[1]["display_name"] == "Unknown"


# ---------------------------------------------------------------------------
# GET /api/leaderboard/me
# ---------------------------------------------------------------------------


class TestGetMyRank:
    def test_my_rank_returns_rank(self, client: TestClient, monkeypatch):
        user_id = "uid-ranked"
        email = "ranked@test.com"

        async def mock_get_rank(uid):
            return 2  # 0-based

        async def mock_get_score(uid):
            return 42.0

        async def mock_get_count():
            return 10

        monkeypatch.setattr("app.db.cache.get_leaderboard_rank", mock_get_rank)
        monkeypatch.setattr("app.db.cache.get_leaderboard_score", mock_get_score)
        monkeypatch.setattr("app.db.cache.get_leaderboard_count", mock_get_count)

        token = make_token(sub=user_id, email=email)
        resp = client.get(
            "/api/leaderboard/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["rank"] == 3
        assert body["total_points"] == 42
        assert body["total_participants"] == 10

    def test_my_rank_unranked_returns_404(self, client: TestClient, monkeypatch):
        user_id = "uid-unranked"
        email = "unranked@test.com"

        async def mock_get_rank(uid):
            return None

        async def mock_get_score(uid):
            return None

        async def mock_get_count():
            return 5

        monkeypatch.setattr("app.db.cache.get_leaderboard_rank", mock_get_rank)
        monkeypatch.setattr("app.db.cache.get_leaderboard_score", mock_get_score)
        monkeypatch.setattr("app.db.cache.get_leaderboard_count", mock_get_count)

        token = make_token(sub=user_id, email=email)
        resp = client.get(
            "/api/leaderboard/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert resp.status_code == 404

    def test_my_rank_unauthenticated_returns_401(self, client: TestClient):
        resp = client.get("/api/leaderboard/me")

        assert resp.status_code in (401, 403)
