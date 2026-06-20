import pytest
from fastapi.testclient import TestClient

from app.models.bracket import SlotPrediction
from tests.conftest import make_token


def sp(teams: list[str], winner: str, **kwargs) -> SlotPrediction:
    return SlotPrediction(teams=teams, winner=winner, **kwargs)


def _seed_user(
    client: TestClient,
    sub: str = "user-sub-123",
    email: str = "test@example.com",
) -> None:
    token = make_token(sub=sub, email=email)
    resp = client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


@pytest.fixture
def r32_seed() -> dict[str, tuple[str, str]]:
    return {f"R32-{i}": (f"T{2*i-1:02d}", f"T{2*i:02d}") for i in range(1, 17)}


@pytest.fixture(autouse=True)
def patch_r32_matchups(monkeypatch, r32_seed):
    """Replace load_r32_matchups with a deterministic seed for all bracket API tests."""
    monkeypatch.setattr(
        "app.bracket.r32_matchups.load_r32_matchups",
        lambda: r32_seed,
    )
    # Also patch it where it's imported in the service module
    monkeypatch.setattr(
        "app.services.brackets.load_r32_matchups",
        lambda: r32_seed,
    )


@pytest.fixture
def valid_predictions() -> dict[str, dict]:
    """
    Bracket where each match the first-listed (odd-numbered) team wins.
    Serialized to JSON-compatible dicts for use in request payloads.
    """
    preds: dict[str, SlotPrediction] = {}

    # R32 — winner-only
    for i in range(1, 17):
        home, away = f"T{2*i-1:02d}", f"T{2*i:02d}"
        preds[f"R32-{i}"] = sp([home, away], home)

    # R16 — winner-only
    r16_teams = [
        ("T01", "T03"), ("T05", "T07"), ("T09", "T11"), ("T13", "T15"),
        ("T17", "T19"), ("T21", "T23"), ("T25", "T27"), ("T29", "T31"),
    ]
    for i, (h, a) in enumerate(r16_teams, 1):
        preds[f"R16-{i}"] = sp([h, a], h)

    # QF — winner-only
    qf_teams = [("T01", "T05"), ("T09", "T13"), ("T17", "T21"), ("T25", "T29")]
    for i, (h, a) in enumerate(qf_teams, 1):
        preds[f"QF-{i}"] = sp([h, a], h)

    # SF — score-bearing, decisive
    preds["SF-1"] = sp(["T01", "T09"], "T01", scores={"T01": 2, "T09": 1})
    preds["SF-2"] = sp(["T17", "T25"], "T17", scores={"T17": 2, "T25": 0})

    # FINAL — score-bearing, level at 90' → PK
    preds["FINAL"] = sp(
        ["T01", "T17"],
        "T01",
        scores={"T01": 1, "T17": 1},
        pk_winner="T01",
        pk_scores={"T01": 4, "T17": 3},
    )

    # TP — winner-only (SF losers: T09 from SF-1, T25 from SF-2)
    preds["TP"] = sp(["T09", "T25"], "T09")

    return {slot: pred.model_dump(exclude_none=True) for slot, pred in preds.items()}


class TestCreateBracket:
    def test_create_bracket_returns_201(self, client: TestClient, valid_predictions):
        _seed_user(client)
        token = make_token()
        resp = client.post(
            "/api/brackets",
            json={"predictions": valid_predictions},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["bracket_id"] != ""
        assert data["user_id"] == "user-sub-123"
        assert data["status"] == "submitted"
        assert data["total_points"] == 0
        assert data["created_at"] != ""
        assert "predictions" in data

    def test_create_bracket_updates_user_record(self, client: TestClient, valid_predictions):
        _seed_user(client)
        token = make_token()
        post_resp = client.post(
            "/api/brackets",
            json={"predictions": valid_predictions},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert post_resp.status_code == 201
        bracket_id = post_resp.json()["bracket_id"]

        me_resp = client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
        assert me_resp.status_code == 200
        assert me_resp.json()["bracket_id"] == bracket_id

    def test_validation_error_returns_400(self, client: TestClient, valid_predictions):
        _seed_user(client)
        token = make_token()
        incomplete = dict(valid_predictions)
        del incomplete["FINAL"]
        resp = client.post(
            "/api/brackets",
            json={"predictions": incomplete},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400

    def test_invalid_winner_returns_400(self, client: TestClient, valid_predictions):
        _seed_user(client)
        token = make_token()
        bad = dict(valid_predictions)
        bad["R32-1"] = {"teams": ["T01", "T02"], "winner": "GER"}
        resp = client.post(
            "/api/brackets",
            json={"predictions": bad},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400

    def test_duplicate_bracket_returns_409(self, client: TestClient, valid_predictions):
        _seed_user(client)
        token = make_token()
        first = client.post(
            "/api/brackets",
            json={"predictions": valid_predictions},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert first.status_code == 201

        second = client.post(
            "/api/brackets",
            json={"predictions": valid_predictions},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert second.status_code == 409

    def test_unauthenticated_returns_401(self, client: TestClient, valid_predictions):
        resp = client.post(
            "/api/brackets",
            json={"predictions": valid_predictions},
        )
        assert resp.status_code == 401
