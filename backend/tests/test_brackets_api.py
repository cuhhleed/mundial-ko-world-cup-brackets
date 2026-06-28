import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.db.dynamo import get_table
from app.models.bracket import SlotPrediction
from tests.conftest import make_token


def sp(teams: list[str], winner: str, **kwargs) -> SlotPrediction:
    return SlotPrediction(teams=teams, winner=winner, **kwargs)


def _seed_match(
    match_id: str,
    round: str,
    home: str,
    away: str,
    home_score: int | None = None,
    away_score: int | None = None,
    pk_home_score: int | None = None,
    pk_away_score: int | None = None,
    pk_winner: str | None = None,
    status: str = "scheduled",
) -> None:
    item: dict = {
        "match_id": match_id,
        "round": round,
        "match_number": 1,
        "home_team": home,
        "away_team": away,
        "status": status,
        "kickoff_time": "2026-06-28T16:00:00Z",
    }
    if home_score is not None:
        item["home_score"] = home_score
    if away_score is not None:
        item["away_score"] = away_score
    if pk_home_score is not None:
        item["pk_home_score"] = pk_home_score
    if pk_away_score is not None:
        item["pk_away_score"] = pk_away_score
    if pk_winner is not None:
        item["pk_winner"] = pk_winner
    get_table(settings.MATCHES_TABLE).put_item(Item=item)


def _seed_user(
    sub: str = "user-sub-123",
    email: str = "test@example.com",
) -> None:
    from app.services.users import create as create_user

    create_user(sub, email)


@pytest.fixture
def r32_seed() -> dict[str, tuple[str, str]]:
    return {f"R32-{i}": (f"T{2 * i - 1:02d}", f"T{2 * i:02d}") for i in range(1, 17)}


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
        home, away = f"T{2 * i - 1:02d}", f"T{2 * i:02d}"
        preds[f"R32-{i}"] = sp([home, away], home)

    # R16 — winner-only (corrected feeder tree)
    r16_teams = [
        ("T01", "T07"),  # R16-1: R32-1 winner vs R32-4 winner
        ("T05", "T11"),  # R16-2: R32-3 winner vs R32-6 winner
        ("T03", "T09"),  # R16-3: R32-2 winner vs R32-5 winner
        ("T13", "T15"),  # R16-4: R32-7 winner vs R32-8 winner
        ("T23", "T21"),  # R16-5: R32-12 winner vs R32-11 winner
        ("T19", "T17"),  # R16-6: R32-10 winner vs R32-9 winner
        ("T29", "T27"),  # R16-7: R32-15 winner vs R32-14 winner
        ("T25", "T31"),  # R16-8: R32-13 winner vs R32-16 winner
    ]
    for i, (h, a) in enumerate(r16_teams, 1):
        preds[f"R16-{i}"] = sp([h, a], h)

    # QF — winner-only (QF-1←R16-1/R16-2, QF-2←R16-5/R16-6, QF-3←R16-3/R16-4, QF-4←R16-7/R16-8)
    qf_teams = [
        ("T01", "T05"),  # QF-1: R16-1 winner vs R16-2 winner
        ("T23", "T19"),  # QF-2: R16-5 winner vs R16-6 winner
        ("T03", "T13"),  # QF-3: R16-3 winner vs R16-4 winner
        ("T29", "T25"),  # QF-4: R16-7 winner vs R16-8 winner
    ]
    for i, (h, a) in enumerate(qf_teams, 1):
        preds[f"QF-{i}"] = sp([h, a], h)

    # SF — score-bearing, decisive
    preds["SF-1"] = sp(["T01", "T23"], "T01", scores={"T01": 2, "T23": 1})
    preds["SF-2"] = sp(["T03", "T29"], "T03", scores={"T03": 2, "T29": 0})

    # FINAL — score-bearing, level at 90' → PK
    preds["FINAL"] = sp(
        ["T01", "T03"],
        "T01",
        scores={"T01": 1, "T03": 1},
        pk_winner="T01",
        pk_scores={"T01": 4, "T03": 3},
    )

    # TP — winner-only (SF losers: T23 from SF-1, T29 from SF-2)
    preds["TP"] = sp(["T23", "T29"], "T23")

    return {slot: pred.model_dump(exclude_none=True) for slot, pred in preds.items()}


class TestCreateBracket:
    def test_create_bracket_returns_201(self, client: TestClient, valid_predictions):
        _seed_user()
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

    def test_create_bracket_updates_user_record(
        self, client: TestClient, valid_predictions
    ):
        _seed_user()
        token = make_token()
        post_resp = client.post(
            "/api/brackets",
            json={"predictions": valid_predictions},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert post_resp.status_code == 201
        bracket_id = post_resp.json()["bracket_id"]

        me_resp = client.get(
            "/api/users/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert me_resp.status_code == 200
        assert me_resp.json()["bracket_id"] == bracket_id

    def test_validation_error_returns_400(self, client: TestClient, valid_predictions):
        _seed_user()
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
        _seed_user()
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
        _seed_user()
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


class TestLateBracket:
    def test_late_bracket_with_locked_slots_returns_201(
        self, client: TestClient, valid_predictions
    ):
        _seed_match(
            "R32-1", "R32", "T01", "T02", home_score=2, away_score=0, status="completed"
        )
        _seed_match(
            "R32-2", "R32", "T03", "T04", home_score=1, away_score=0, status="completed"
        )

        _seed_user()
        token = make_token()
        partial = {
            k: v for k, v in valid_predictions.items() if k not in {"R32-1", "R32-2"}
        }
        resp = client.post(
            "/api/brackets",
            json={"predictions": partial},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert set(data["locked_slots"]) == {"R32-1", "R32-2"}
        assert len(data["predictions"]) == 32

    def test_prediction_for_locked_slot_returns_400(
        self, client: TestClient, valid_predictions
    ):
        _seed_match(
            "R32-1", "R32", "T01", "T02", home_score=2, away_score=0, status="completed"
        )

        _seed_user()
        token = make_token()
        resp = client.post(
            "/api/brackets",
            json={"predictions": valid_predictions},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400

    def test_missing_prediction_for_open_slot_returns_400(
        self, client: TestClient, valid_predictions
    ):
        _seed_match(
            "R32-1", "R32", "T01", "T02", home_score=2, away_score=0, status="completed"
        )

        _seed_user()
        token = make_token()
        # Remove R32-1 (locked) AND R32-3 (open, missing)
        partial = {
            k: v for k, v in valid_predictions.items() if k not in {"R32-1", "R32-3"}
        }
        resp = client.post(
            "/api/brackets",
            json={"predictions": partial},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400


class TestGetBracketById:
    def test_get_bracket_returns_200(self, client: TestClient, valid_predictions):
        _seed_user()
        token = make_token()
        post_resp = client.post(
            "/api/brackets",
            json={"predictions": valid_predictions},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert post_resp.status_code == 201
        bracket_id = post_resp.json()["bracket_id"]

        resp = client.get(f"/api/brackets/{bracket_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["slots"]) == 32
        for slot in data["slots"].values():
            assert "prediction" in slot
            assert slot["result"] is None
            assert slot["points"] is None
        assert data["total_points"] == 0

    def test_get_bracket_not_found_returns_404(self, client: TestClient):
        resp = client.get("/api/brackets/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404

    def test_get_bracket_overlays_completed_match_result(
        self, client: TestClient, valid_predictions
    ):
        _seed_match(
            "R32-1", "R32", "T01", "T02", home_score=2, away_score=0, status="completed"
        )

        _seed_user()
        token = make_token()
        partial = {k: v for k, v in valid_predictions.items() if k != "R32-1"}
        post_resp = client.post(
            "/api/brackets",
            json={"predictions": partial},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert post_resp.status_code == 201
        bracket_id = post_resp.json()["bracket_id"]

        resp = client.get(f"/api/brackets/{bracket_id}")
        assert resp.status_code == 200
        data = resp.json()
        r32_1 = data["slots"]["R32-1"]
        assert r32_1["result"] is not None
        assert r32_1["result"]["winner"] == "T01"
        assert r32_1["result"]["teams"] == ["T01", "T02"]


class TestGetMyBracket:
    def test_get_my_bracket_returns_200(self, client: TestClient, valid_predictions):
        _seed_user()
        token = make_token()
        post_resp = client.post(
            "/api/brackets",
            json={"predictions": valid_predictions},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert post_resp.status_code == 201
        bracket_id = post_resp.json()["bracket_id"]

        resp = client.get(
            "/api/brackets/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        assert resp.json()["bracket_id"] == bracket_id

    def test_get_my_bracket_no_bracket_returns_404(self, client: TestClient):
        _seed_user()
        token = make_token()
        resp = client.get(
            "/api/brackets/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 404

    def test_get_my_bracket_unauthenticated_returns_401(self, client: TestClient):
        resp = client.get("/api/brackets/me")
        assert resp.status_code == 401


class TestScoringIntegration:
    def test_completed_r32_match_scores_correct_winner(
        self, client: TestClient, valid_predictions
    ):
        # Seed a completed R32-1 match where T01 wins 2-0 (T01 is the predicted winner)
        _seed_match(
            "R32-1", "R32", "T01", "T02", home_score=2, away_score=0, status="completed"
        )

        _seed_user()
        token = make_token()
        # R32-1 is completed so omit it from the prediction payload
        partial = {k: v for k, v in valid_predictions.items() if k != "R32-1"}
        post_resp = client.post(
            "/api/brackets",
            json={"predictions": partial},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert post_resp.status_code == 201
        bracket_id = post_resp.json()["bracket_id"]

        resp = client.get(f"/api/brackets/{bracket_id}")
        assert resp.status_code == 200
        data = resp.json()

        # R32-1 is locked — scored=True but 0 pts
        r32_1 = data["slots"]["R32-1"]
        assert r32_1["points"] == 0

        # total_points reflects locked slot (0 pts for locked) plus all other unscored slots (None)
        assert data["total_points"] == 0


class TestBracketTemplate:
    def test_template_with_no_matches_all_open(self, client: TestClient):
        resp = client.get("/api/brackets/template")
        assert resp.status_code == 200
        data = resp.json()
        assert "slots" in data
        for slot_data in data["slots"].values():
            assert slot_data["status"] == "open"
            assert slot_data["result"] is None

    def test_template_shows_correct_locked_and_open_statuses(self, client: TestClient):
        _seed_match(
            "R32-1", "R32", "T01", "T02", home_score=2, away_score=0, status="completed"
        )
        _seed_match("R32-2", "R32", "T03", "T04", status="scheduled")

        resp = client.get("/api/brackets/template")
        assert resp.status_code == 200
        data = resp.json()
        slots = data["slots"]

        assert slots["R32-1"]["status"] == "locked"
        assert slots["R32-1"]["result"] is not None
        assert slots["R32-1"]["result"]["winner"] == "T01"

        assert slots["R32-2"]["status"] == "open"
        assert slots["R32-2"]["teams"] == ["T03", "T04"]
        assert slots["R32-2"]["result"] is None

    def test_template_unauthenticated_returns_200(self, client: TestClient):
        resp = client.get("/api/brackets/template")
        assert resp.status_code == 200

    def test_template_r16_with_placeholder_match_returns_null_teams(self, client: TestClient):
        _seed_match("R16-1", "R16", "RD32", "RD32", status="scheduled")

        resp = client.get("/api/brackets/template")
        assert resp.status_code == 200
        slots = resp.json()["slots"]

        assert slots["R16-1"]["teams"] is None
        assert slots["R16-1"]["status"] == "open"

    def test_template_r16_derives_teams_from_locked_feeders(self, client: TestClient):
        _seed_match("R32-1", "R32", "T01", "T02", home_score=2, away_score=0, status="completed")
        _seed_match("R32-4", "R32", "T07", "T08", home_score=1, away_score=0, status="completed")
        _seed_match("R16-1", "R16", "RD32", "RD32", status="scheduled")

        resp = client.get("/api/brackets/template")
        assert resp.status_code == 200
        slots = resp.json()["slots"]

        assert slots["R16-1"]["teams"] == ["T01", "T07"]

    def test_template_r16_null_when_one_feeder_locked(self, client: TestClient):
        _seed_match("R32-1", "R32", "T01", "T02", home_score=2, away_score=0, status="completed")
        _seed_match("R32-4", "R32", "T07", "T08", status="scheduled")
        _seed_match("R16-1", "R16", "RD32", "RD32", status="scheduled")

        resp = client.get("/api/brackets/template")
        assert resp.status_code == 200
        slots = resp.json()["slots"]

        assert slots["R16-1"]["teams"] is None

    def test_template_r32_scheduled_still_shows_teams(self, client: TestClient):
        _seed_match("R32-5", "R32", "T09", "T10", status="scheduled")

        resp = client.get("/api/brackets/template")
        assert resp.status_code == 200
        slots = resp.json()["slots"]

        assert slots["R32-5"]["teams"] == ["T09", "T10"]
