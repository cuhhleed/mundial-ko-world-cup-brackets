import pytest

from app.bracket.scoring import SlotScore, score_slot
from app.models.bracket import SlotPrediction


def sp(teams: list[str], winner: str, **kwargs) -> SlotPrediction:
    return SlotPrediction(teams=teams, winner=winner, **kwargs)


# ---------------------------------------------------------------------------
# Basic correctness
# ---------------------------------------------------------------------------

class TestCorrectWinnerWrongScore:
    def test_sf_correct_winner_wrong_score(self):
        prediction = sp(["BRA", "ARG"], "BRA", scores={"BRA": 1, "ARG": 0})
        result = sp(["BRA", "ARG"], "BRA", scores={"BRA": 3, "ARG": 1})
        slot_score = score_slot("SF-1", prediction, result, [])
        assert slot_score.scored is True
        assert slot_score.winner_points == 16
        assert slot_score.score_points == 0
        assert slot_score.pk_score_points == 0
        assert slot_score.total == 16


class TestCorrectWinnerAndScore:
    def test_sf_correct_winner_and_score(self):
        prediction = sp(["BRA", "ARG"], "BRA", scores={"BRA": 2, "ARG": 1})
        result = sp(["BRA", "ARG"], "BRA", scores={"BRA": 2, "ARG": 1})
        slot_score = score_slot("SF-1", prediction, result, [])
        assert slot_score.scored is True
        assert slot_score.winner_points == 16
        assert slot_score.score_points == 16
        assert slot_score.pk_score_points == 0
        assert slot_score.total == 32


class TestCorrectWinnerScoreAndPK:
    def test_final_correct_winner_score_and_pk(self):
        prediction = sp(
            ["BRA", "ARG"],
            "BRA",
            scores={"BRA": 1, "ARG": 1},
            pk_winner="BRA",
            pk_scores={"BRA": 4, "ARG": 3},
        )
        result = sp(
            ["BRA", "ARG"],
            "BRA",
            scores={"BRA": 1, "ARG": 1},
            pk_winner="BRA",
            pk_scores={"BRA": 4, "ARG": 3},
        )
        slot_score = score_slot("FINAL", prediction, result, [])
        assert slot_score.scored is True
        assert slot_score.winner_points == 32
        assert slot_score.score_points == 32
        assert slot_score.pk_score_points == 40
        assert slot_score.total == 104


class TestWrongWinner:
    def test_wrong_winner_earns_zero(self):
        prediction = sp(["BRA", "ARG"], "ARG")
        result = sp(["BRA", "ARG"], "BRA")
        slot_score = score_slot("R32-1", prediction, result, [])
        assert slot_score.scored is True
        assert slot_score.winner_points == 0
        assert slot_score.total == 0


class TestWrongMatchupCorrectWinner:
    def test_qf_wrong_matchup_correct_winner_earns_full_winner_pts(self):
        # Prediction has different teams but same winner as result
        prediction = sp(["BRA", "FRA"], "BRA")
        result = sp(["BRA", "ARG"], "BRA")
        slot_score = score_slot("QF-1", prediction, result, [])
        assert slot_score.scored is True
        assert slot_score.winner_points == 8
        assert slot_score.total == 8


class TestLockedSlot:
    def test_locked_slot_scores_true_with_zero_points(self):
        prediction = sp(["BRA", "ARG"], "BRA")
        result = sp(["BRA", "ARG"], "BRA")
        slot_score = score_slot("R32-1", prediction, result, ["R32-1"])
        assert slot_score.scored is True
        assert slot_score.winner_points == 0
        assert slot_score.total == 0

    def test_locked_slot_ignores_prediction_vs_result(self):
        # Even when prediction matches result, locked yields 0 pts
        prediction = sp(["X", "Y"], "X")
        result = sp(["X", "Y"], "X")
        slot_score = score_slot("R32-5", prediction, result, ["R32-5"])
        assert slot_score.scored is True
        assert slot_score.total == 0


class TestNoResult:
    def test_no_result_returns_not_scored(self):
        prediction = sp(["BRA", "ARG"], "BRA")
        slot_score = score_slot("R32-1", prediction, None, [])
        assert slot_score.scored is False
        assert slot_score.total == 0


# ---------------------------------------------------------------------------
# Parametrized correct-winner across all rounds
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("slot_id, expected_pts", [
    ("R32-1",  2),
    ("R16-1",  4),
    ("QF-1",   8),
    ("SF-1",  16),
    ("FINAL", 32),
    ("TP",    10),
])
def test_correct_winner_points_per_round(slot_id: str, expected_pts: int):
    prediction = sp(["BRA", "ARG"], "BRA")
    result = sp(["BRA", "ARG"], "BRA")
    slot_score = score_slot(slot_id, prediction, result, [])
    assert slot_score.scored is True
    assert slot_score.winner_points == expected_pts
    assert slot_score.total == expected_pts


# ---------------------------------------------------------------------------
# PK edge cases
# ---------------------------------------------------------------------------

class TestPKEdgeCases:
    def test_pk_prediction_exists_but_match_was_decisive(self):
        """User predicted a draw + PK, but match was decisive — no PK pts."""
        prediction = sp(
            ["BRA", "ARG"],
            "BRA",
            scores={"BRA": 1, "ARG": 1},
            pk_winner="BRA",
            pk_scores={"BRA": 4, "ARG": 3},
        )
        # Result: decisive win (no pk_scores)
        result = sp(["BRA", "ARG"], "BRA", scores={"BRA": 2, "ARG": 1})
        slot_score = score_slot("SF-1", prediction, result, [])
        assert slot_score.pk_score_points == 0

    def test_match_went_to_pks_but_user_predicted_decisive(self):
        """Match went to PKs but user had no pk_scores — no PK pts, winner pts if correct."""
        prediction = sp(["BRA", "ARG"], "BRA", scores={"BRA": 2, "ARG": 1})
        result = sp(
            ["BRA", "ARG"],
            "BRA",
            scores={"BRA": 1, "ARG": 1},
            pk_winner="BRA",
            pk_scores={"BRA": 4, "ARG": 3},
        )
        slot_score = score_slot("FINAL", prediction, result, [])
        assert slot_score.pk_score_points == 0
        assert slot_score.winner_points == 32  # correct winner still earns pts

    def test_correct_pk_winner_wrong_pk_scoreline(self):
        """User got PK winner right but wrong scoreline — no PK pts."""
        prediction = sp(
            ["BRA", "ARG"],
            "BRA",
            scores={"BRA": 1, "ARG": 1},
            pk_winner="BRA",
            pk_scores={"BRA": 5, "ARG": 3},  # wrong scoreline
        )
        result = sp(
            ["BRA", "ARG"],
            "BRA",
            scores={"BRA": 1, "ARG": 1},
            pk_winner="BRA",
            pk_scores={"BRA": 4, "ARG": 3},
        )
        slot_score = score_slot("FINAL", prediction, result, [])
        assert slot_score.pk_score_points == 0
        assert slot_score.winner_points == 32
        assert slot_score.score_points == 32
        assert slot_score.total == 64
