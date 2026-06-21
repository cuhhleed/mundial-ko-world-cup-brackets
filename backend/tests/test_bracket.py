import copy

import pytest

from app.models.bracket import SlotPrediction
from app.bracket.derivation import (
    derive_matchup,
    derive_all_matchups,
    predicted_loser,
    validate_bracket,
)


def sp(teams: list[str], winner: str, **kwargs) -> SlotPrediction:
    return SlotPrediction(teams=teams, winner=winner, **kwargs)


@pytest.fixture
def r32_seed() -> dict[str, tuple[str, str]]:
    return {f"R32-{i}": (f"T{2*i-1:02d}", f"T{2*i:02d}") for i in range(1, 17)}


@pytest.fixture
def valid_predictions() -> dict[str, SlotPrediction]:
    """
    Bracket where each match the first-listed (odd-numbered) team wins.
    R32: T01 beats T02, T03 beats T04, ..., T31 beats T32.
    R16: T01 beats T03, T05 beats T07, T09 beats T11, T13 beats T15,
         T17 beats T19, T21 beats T23, T25 beats T27, T29 beats T31.
    QF:  T01 beats T05, T09 beats T13, T17 beats T21, T25 beats T29.
    SF:  T01 beats T09 (2-1), T17 beats T25 (2-0).
    FIN: T01 beats T17 on PK (1-1 aet, 4-3 pk).
    TP:  T09 beats T25 (SF losers).
    """
    preds: dict[str, SlotPrediction] = {}

    # R32 — winner-only
    for i in range(1, 17):
        home, away = f"T{2*i-1:02d}", f"T{2*i:02d}"
        preds[f"R32-{i}"] = sp([home, away], home)

    # R16 — winner-only
    # R16-k feeds from R32-(2k-1) and R32-(2k)
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

    return preds


# ---------------------------------------------------------------------------
# derive_matchup
# ---------------------------------------------------------------------------


class TestDeriveMatchup:
    def test_r32_slot_returns_seed_matchup(self, r32_seed):
        assert derive_matchup("R32-1", {}, r32_seed) == ("T01", "T02")
        assert derive_matchup("R32-16", {}, r32_seed) == ("T31", "T32")

    def test_r16_derived_from_r32_winners(self, r32_seed, valid_predictions):
        result = derive_matchup("R16-1", valid_predictions, r32_seed)
        assert result == ("T01", "T03")

    def test_qf_cascades_through_r16(self, r32_seed, valid_predictions):
        result = derive_matchup("QF-1", valid_predictions, r32_seed)
        assert result == ("T01", "T05")

    def test_sf_cascades_through_qf(self, r32_seed, valid_predictions):
        result = derive_matchup("SF-1", valid_predictions, r32_seed)
        assert result == ("T01", "T09")

    def test_final_cascades_through_sf(self, r32_seed, valid_predictions):
        result = derive_matchup("FINAL", valid_predictions, r32_seed)
        assert result == ("T01", "T17")

    def test_returns_none_when_upstream_not_predicted(self, r32_seed, valid_predictions):
        preds = copy.deepcopy(valid_predictions)
        del preds["R32-1"]
        assert derive_matchup("R16-1", preds, r32_seed) is None

    def test_returns_none_when_intermediate_slot_missing(self, r32_seed, valid_predictions):
        preds = copy.deepcopy(valid_predictions)
        del preds["QF-1"]
        assert derive_matchup("SF-1", preds, r32_seed) is None


# ---------------------------------------------------------------------------
# predicted_loser / TP derivation
# ---------------------------------------------------------------------------


class TestPredictedLoser:
    def test_returns_non_winner(self, valid_predictions):
        assert predicted_loser("SF-1", valid_predictions) == "T09"
        assert predicted_loser("SF-2", valid_predictions) == "T25"

    def test_returns_none_for_missing_slot(self, valid_predictions):
        assert predicted_loser("R32-99", valid_predictions) is None

    def test_tp_teams_derived_from_sf_losers(self, r32_seed, valid_predictions):
        result = derive_matchup("TP", valid_predictions, r32_seed)
        assert result == ("T09", "T25")


# ---------------------------------------------------------------------------
# derive_all_matchups
# ---------------------------------------------------------------------------


class TestDeriveAllMatchups:
    def test_returns_all_32_slots(self, r32_seed, valid_predictions):
        result = derive_all_matchups(valid_predictions, r32_seed)
        assert len(result) == 32

    def test_r32_matchup_matches_seed(self, r32_seed, valid_predictions):
        result = derive_all_matchups(valid_predictions, r32_seed)
        assert result["R32-1"] == ("T01", "T02")

    def test_final_matchup_correctly_cascaded(self, r32_seed, valid_predictions):
        result = derive_all_matchups(valid_predictions, r32_seed)
        assert result["FINAL"] == ("T01", "T17")


# ---------------------------------------------------------------------------
# validate_bracket
# ---------------------------------------------------------------------------


class TestValidateBracket:
    def test_valid_bracket_passes(self, r32_seed, valid_predictions):
        errors = validate_bracket(valid_predictions, r32_seed)
        assert errors == []

    def test_missing_slot_reported(self, r32_seed, valid_predictions):
        preds = copy.deepcopy(valid_predictions)
        del preds["QF-1"]
        errors = validate_bracket(preds, r32_seed)
        assert any("Missing" in e for e in errors)

    def test_forged_r16_matchup_fails(self, r32_seed, valid_predictions):
        preds = copy.deepcopy(valid_predictions)
        # Store teams that don't match feeder winners (T01 and T03 are correct; forge T02)
        preds["R16-1"] = sp(["T01", "T02"], "T01")
        errors = validate_bracket(preds, r32_seed)
        assert any("R16-1" in e and "do not match" in e for e in errors)

    def test_r32_teams_not_matching_seed_fails(self, r32_seed, valid_predictions):
        preds = copy.deepcopy(valid_predictions)
        preds["R32-1"] = sp(["ARG", "FRA"], "ARG")
        errors = validate_bracket(preds, r32_seed)
        assert any("R32-1" in e and "do not match" in e for e in errors)

    def test_winner_not_in_teams_fails(self, r32_seed, valid_predictions):
        preds = copy.deepcopy(valid_predictions)
        preds["R32-3"] = sp(["T05", "T06"], "GER")
        errors = validate_bracket(preds, r32_seed)
        assert any("R32-3" in e and "winner" in e and "not in teams" in e for e in errors)

    def test_missing_scores_on_sf_fails(self, r32_seed, valid_predictions):
        preds = copy.deepcopy(valid_predictions)
        preds["SF-1"] = sp(["T01", "T09"], "T01")
        errors = validate_bracket(preds, r32_seed)
        assert any("SF-1" in e and "requires scores" in e for e in errors)

    def test_missing_scores_on_final_fails(self, r32_seed, valid_predictions):
        preds = copy.deepcopy(valid_predictions)
        preds["FINAL"] = sp(["T01", "T17"], "T01")
        errors = validate_bracket(preds, r32_seed)
        assert any("FINAL" in e and "requires scores" in e for e in errors)

    def test_scores_present_on_r32_slot_fails(self, r32_seed, valid_predictions):
        preds = copy.deepcopy(valid_predictions)
        preds["R32-1"] = sp(["T01", "T02"], "T01", scores={"T01": 2, "T02": 0})
        errors = validate_bracket(preds, r32_seed)
        assert any("R32-1" in e and "must not have scores" in e for e in errors)

    def test_scores_present_on_tp_slot_fails(self, r32_seed, valid_predictions):
        preds = copy.deepcopy(valid_predictions)
        preds["TP"] = sp(["T09", "T25"], "T09", scores={"T09": 1, "T25": 0})
        errors = validate_bracket(preds, r32_seed)
        assert any("TP" in e and "must not have scores" in e for e in errors)

    def test_level_scores_without_pk_winner_fails(self, r32_seed, valid_predictions):
        preds = copy.deepcopy(valid_predictions)
        preds["FINAL"] = sp(["T01", "T17"], "T01", scores={"T01": 1, "T17": 1})
        errors = validate_bracket(preds, r32_seed)
        assert any("FINAL" in e and "pk_winner" in e for e in errors)

    def test_pk_winner_mismatch_fails(self, r32_seed, valid_predictions):
        preds = copy.deepcopy(valid_predictions)
        # winner is T01 but pk_winner is T17
        preds["SF-2"] = sp(
            ["T17", "T25"],
            "T17",
            scores={"T17": 0, "T25": 0},
            pk_winner="T25",
            pk_scores={"T17": 2, "T25": 3},
        )
        errors = validate_bracket(preds, r32_seed)
        assert any("SF-2" in e and "pk_winner must equal winner" in e for e in errors)

    def test_pk_winner_must_have_higher_pk_score(self, r32_seed, valid_predictions):
        preds = copy.deepcopy(valid_predictions)
        preds["FINAL"] = sp(
            ["T01", "T17"],
            "T01",
            scores={"T01": 1, "T17": 1},
            pk_winner="T01",
            pk_scores={"T01": 3, "T17": 3},
        )
        errors = validate_bracket(preds, r32_seed)
        assert any("FINAL" in e and "strictly higher pk_score" in e for e in errors)

    def test_pk_present_on_decisive_result_fails(self, r32_seed, valid_predictions):
        preds = copy.deepcopy(valid_predictions)
        preds["SF-1"] = sp(
            ["T01", "T09"],
            "T01",
            scores={"T01": 2, "T09": 1},
            pk_winner="T01",
            pk_scores={"T01": 4, "T09": 2},
        )
        errors = validate_bracket(preds, r32_seed)
        assert any("SF-1" in e and "PK fields must be absent" in e for e in errors)
