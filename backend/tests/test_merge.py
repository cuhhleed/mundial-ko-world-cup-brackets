import pytest

from app.bracket.merge import MergePredictionsError, merge_predictions
from app.models.bracket import SlotPrediction
from app.models.match import Match


def sp(teams: list[str], winner: str, **kwargs) -> SlotPrediction:
    return SlotPrediction(teams=teams, winner=winner, **kwargs)


def make_match(
    match_id: str,
    round: str,
    home: str,
    away: str,
    home_score: int | None = None,
    away_score: int | None = None,
    pk_home_score: int | None = None,
    pk_away_score: int | None = None,
    pk_winner: str | None = None,
    status: str = "completed",
) -> Match:
    return Match(
        match_id=match_id,
        round=round,
        match_number=1,
        home_team=home,
        away_team=away,
        home_score=home_score,
        away_score=away_score,
        pk_home_score=pk_home_score,
        pk_away_score=pk_away_score,
        pk_winner=pk_winner,
        status=status,
        kickoff_time="2026-06-28T16:00:00Z",
    )


@pytest.fixture
def full_user_predictions() -> dict[str, SlotPrediction]:
    """Full 32-slot bracket — odd-numbered team wins each match."""
    preds: dict[str, SlotPrediction] = {}

    for i in range(1, 17):
        home, away = f"T{2 * i - 1:02d}", f"T{2 * i:02d}"
        preds[f"R32-{i}"] = sp([home, away], home)

    r16_teams = [
        ("T01", "T03"),
        ("T05", "T07"),
        ("T09", "T11"),
        ("T13", "T15"),
        ("T17", "T19"),
        ("T21", "T23"),
        ("T25", "T27"),
        ("T29", "T31"),
    ]
    for i, (h, a) in enumerate(r16_teams, 1):
        preds[f"R16-{i}"] = sp([h, a], h)

    qf_teams = [("T01", "T05"), ("T09", "T13"), ("T17", "T21"), ("T25", "T29")]
    for i, (h, a) in enumerate(qf_teams, 1):
        preds[f"QF-{i}"] = sp([h, a], h)

    preds["SF-1"] = sp(["T01", "T09"], "T01", scores={"T01": 2, "T09": 1})
    preds["SF-2"] = sp(["T17", "T25"], "T17", scores={"T17": 2, "T25": 0})
    preds["FINAL"] = sp(
        ["T01", "T17"],
        "T01",
        scores={"T01": 1, "T17": 1},
        pk_winner="T01",
        pk_scores={"T01": 4, "T17": 3},
    )
    preds["TP"] = sp(["T09", "T25"], "T09")

    return preds


class TestNoCompletedMatches:
    def test_returns_user_predictions_unchanged(self, full_user_predictions):
        merged, locked = merge_predictions(full_user_predictions, {})
        assert merged == full_user_predictions
        assert locked == []


class TestTwoCompletedR32Matches:
    def test_merged_result_has_32_slots_and_two_locked(self, full_user_predictions):
        completed = {
            "R32-1": make_match("R32-1", "R32", "T01", "T02", home_score=2, away_score=0),
            "R32-2": make_match("R32-2", "R32", "T03", "T04", home_score=1, away_score=0),
        }
        user_preds = {k: v for k, v in full_user_predictions.items() if k not in completed}

        merged, locked = merge_predictions(user_preds, completed)

        assert len(merged) == 32
        assert set(locked) == {"R32-1", "R32-2"}

    def test_locked_slots_use_actual_result(self, full_user_predictions):
        completed = {
            "R32-1": make_match("R32-1", "R32", "T01", "T02", home_score=0, away_score=2),
        }
        user_preds = {k: v for k, v in full_user_predictions.items() if k != "R32-1"}

        merged, _ = merge_predictions(user_preds, completed)

        locked_pred = merged["R32-1"]
        assert locked_pred.winner == "T02"
        assert locked_pred.teams == ["T01", "T02"]


class TestNonScoreBearingLockedSlot:
    def test_no_scores_on_r32_locked_slot(self, full_user_predictions):
        completed = {
            "R32-3": make_match("R32-3", "R32", "T05", "T06", home_score=3, away_score=1),
        }
        user_preds = {k: v for k, v in full_user_predictions.items() if k != "R32-3"}

        merged, _ = merge_predictions(user_preds, completed)

        pred = merged["R32-3"]
        assert pred.scores is None
        assert pred.pk_winner is None
        assert pred.pk_scores is None

    def test_no_scores_on_qf_locked_slot(self, full_user_predictions):
        completed = {
            "QF-1": make_match("QF-1", "QF", "T01", "T05", home_score=1, away_score=0),
        }
        user_preds = {k: v for k, v in full_user_predictions.items() if k != "QF-1"}

        merged, _ = merge_predictions(user_preds, completed)

        pred = merged["QF-1"]
        assert pred.scores is None
        assert pred.pk_winner is None


class TestScoreBearingLockedSlot:
    def test_sf_decisive_includes_scores(self, full_user_predictions):
        completed = {
            "SF-1": make_match("SF-1", "SF", "T01", "T09", home_score=2, away_score=1),
        }
        user_preds = {k: v for k, v in full_user_predictions.items() if k != "SF-1"}

        merged, _ = merge_predictions(user_preds, completed)

        pred = merged["SF-1"]
        assert pred.scores == {"T01": 2, "T09": 1}
        assert pred.winner == "T01"
        assert pred.pk_winner is None
        assert pred.pk_scores is None

    def test_final_with_pks_includes_pk_fields(self, full_user_predictions):
        completed = {
            "FINAL": make_match(
                "FINAL",
                "FINAL",
                "T01",
                "T17",
                home_score=1,
                away_score=1,
                pk_home_score=4,
                pk_away_score=3,
                pk_winner="T01",
            ),
        }
        user_preds = {k: v for k, v in full_user_predictions.items() if k != "FINAL"}

        merged, _ = merge_predictions(user_preds, completed)

        pred = merged["FINAL"]
        assert pred.scores == {"T01": 1, "T17": 1}
        assert pred.pk_winner == "T01"
        assert pred.pk_scores == {"T01": 4, "T17": 3}
        assert pred.winner == "T01"


class TestNonScoreBearingWithPKs:
    def test_pk_fields_stripped_winner_preserved(self, full_user_predictions):
        """R32 match decided on PKs (scores level at 90') — pk fields must not appear."""
        completed = {
            "R32-5": make_match(
                "R32-5",
                "R32",
                "T09",
                "T10",
                home_score=0,
                away_score=0,
                pk_home_score=5,
                pk_away_score=4,
                pk_winner="T09",
            ),
        }
        user_preds = {k: v for k, v in full_user_predictions.items() if k != "R32-5"}

        merged, _ = merge_predictions(user_preds, completed)

        pred = merged["R32-5"]
        assert pred.winner == "T09"
        assert pred.scores is None
        assert pred.pk_winner is None
        assert pred.pk_scores is None


class TestErrorCases:
    def test_prediction_for_locked_slot_raises_error(self, full_user_predictions):
        completed = {
            "R32-1": make_match("R32-1", "R32", "T01", "T02", home_score=2, away_score=0),
        }

        with pytest.raises(MergePredictionsError) as exc_info:
            merge_predictions(full_user_predictions, completed)

        assert any("R32-1" in e and "locked" in e for e in exc_info.value.errors)

    def test_missing_open_slot_prediction_raises_error(self, full_user_predictions):
        user_preds = {k: v for k, v in full_user_predictions.items() if k != "QF-2"}

        with pytest.raises(MergePredictionsError) as exc_info:
            merge_predictions(user_preds, {})

        assert any("QF-2" in e and "missing" in e for e in exc_info.value.errors)


class TestCascading:
    def test_r32_completed_winners_feed_r16_derivation(self, full_user_predictions):
        """R32-1 (T01 wins) and R32-2 (T03 wins) completed; R16-1 must still be correct."""
        completed = {
            "R32-1": make_match("R32-1", "R32", "T01", "T02", home_score=2, away_score=0),
            "R32-2": make_match("R32-2", "R32", "T03", "T04", home_score=1, away_score=0),
        }
        user_preds = {k: v for k, v in full_user_predictions.items() if k not in completed}

        merged, locked = merge_predictions(user_preds, completed)

        assert merged["R32-1"].winner == "T01"
        assert merged["R32-2"].winner == "T03"
        assert set(locked) == {"R32-1", "R32-2"}
        assert merged["R16-1"].teams == ["T01", "T03"]
        assert merged["R16-1"].winner == "T01"
