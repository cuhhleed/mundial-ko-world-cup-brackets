import copy

import pytest

from app.bracket.derivation import (
    derive_all_matchups,
    derive_matchup,
    predicted_loser,
    validate_bracket,
)
from app.models.bracket import SlotPrediction


def sp(teams: list[str], winner: str, **kwargs) -> SlotPrediction:
    return SlotPrediction(teams=teams, winner=winner, **kwargs)


@pytest.fixture
def r32_seed() -> dict[str, tuple[str, str]]:
    return {f"R32-{i}": (f"T{2 * i - 1:02d}", f"T{2 * i:02d}") for i in range(1, 17)}


@pytest.fixture
def valid_predictions() -> dict[str, SlotPrediction]:
    """
    Bracket where each match the first-listed (odd-numbered) team wins.
    R32: T01 beats T02, T03 beats T04, ..., T31 beats T32.
    R32 winners by slot: R32-1→T01, R32-2→T03, R32-3→T05, R32-4→T07,
                         R32-5→T09, R32-6→T11, R32-7→T13, R32-8→T15,
                         R32-9→T17, R32-10→T19, R32-11→T21, R32-12→T23,
                         R32-13→T25, R32-14→T27, R32-15→T29, R32-16→T31.
    R16 (first feeder = home, first-listed wins):
         R16-1=(T01,T07)→T01, R16-2=(T05,T11)→T05, R16-3=(T03,T09)→T03,
         R16-4=(T13,T15)→T13, R16-5=(T23,T21)→T23, R16-6=(T19,T17)→T19,
         R16-7=(T29,T27)→T29, R16-8=(T25,T31)→T25.
    QF (QF-1←R16-1/R16-2, QF-2←R16-5/R16-6, QF-3←R16-3/R16-4, QF-4←R16-7/R16-8):
         QF-1=(T01,T05)→T01, QF-2=(T23,T19)→T23, QF-3=(T03,T13)→T03, QF-4=(T29,T25)→T29.
    SF:  T01 beats T23 (2-1), T03 beats T29 (2-0).
    FIN: T01 beats T03 on PK (1-1 aet, 4-3 pk).
    TP:  T23 beats T29 (SF losers).
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
        assert result == ("T01", "T07")

    def test_qf_cascades_through_r16(self, r32_seed, valid_predictions):
        result = derive_matchup("QF-1", valid_predictions, r32_seed)
        assert result == ("T01", "T05")

    def test_sf_cascades_through_qf(self, r32_seed, valid_predictions):
        result = derive_matchup("SF-1", valid_predictions, r32_seed)
        assert result == ("T01", "T23")

    def test_final_cascades_through_sf(self, r32_seed, valid_predictions):
        result = derive_matchup("FINAL", valid_predictions, r32_seed)
        assert result == ("T01", "T03")

    def test_returns_none_when_upstream_not_predicted(
        self, r32_seed, valid_predictions
    ):
        preds = copy.deepcopy(valid_predictions)
        del preds["R32-1"]
        assert derive_matchup("R16-1", preds, r32_seed) is None

    def test_returns_none_when_intermediate_slot_missing(
        self, r32_seed, valid_predictions
    ):
        preds = copy.deepcopy(valid_predictions)
        del preds["QF-1"]
        assert derive_matchup("SF-1", preds, r32_seed) is None


# ---------------------------------------------------------------------------
# predicted_loser / TP derivation
# ---------------------------------------------------------------------------


class TestPredictedLoser:
    def test_returns_non_winner(self, valid_predictions):
        assert predicted_loser("SF-1", valid_predictions) == "T23"
        assert predicted_loser("SF-2", valid_predictions) == "T29"

    def test_returns_none_for_missing_slot(self, valid_predictions):
        assert predicted_loser("R32-99", valid_predictions) is None

    def test_tp_teams_derived_from_sf_losers(self, r32_seed, valid_predictions):
        result = derive_matchup("TP", valid_predictions, r32_seed)
        assert result == ("T23", "T29")


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
        assert result["FINAL"] == ("T01", "T03")


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
        # Store teams that don't match feeder winners (T01 and T07 are correct; forge T03)
        preds["R16-1"] = sp(["T01", "T03"], "T01")
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
        assert any(
            "R32-3" in e and "winner" in e and "not in teams" in e for e in errors
        )

    def test_missing_scores_on_sf_fails(self, r32_seed, valid_predictions):
        preds = copy.deepcopy(valid_predictions)
        preds["SF-1"] = sp(["T01", "T23"], "T01")
        errors = validate_bracket(preds, r32_seed)
        assert any("SF-1" in e and "requires scores" in e for e in errors)

    def test_missing_scores_on_final_fails(self, r32_seed, valid_predictions):
        preds = copy.deepcopy(valid_predictions)
        preds["FINAL"] = sp(["T01", "T03"], "T01")
        errors = validate_bracket(preds, r32_seed)
        assert any("FINAL" in e and "requires scores" in e for e in errors)

    def test_scores_present_on_r32_slot_fails(self, r32_seed, valid_predictions):
        preds = copy.deepcopy(valid_predictions)
        preds["R32-1"] = sp(["T01", "T02"], "T01", scores={"T01": 2, "T02": 0})
        errors = validate_bracket(preds, r32_seed)
        assert any("R32-1" in e and "must not have scores" in e for e in errors)

    def test_scores_present_on_tp_slot_fails(self, r32_seed, valid_predictions):
        preds = copy.deepcopy(valid_predictions)
        preds["TP"] = sp(["T23", "T29"], "T23", scores={"T23": 1, "T29": 0})
        errors = validate_bracket(preds, r32_seed)
        assert any("TP" in e and "must not have scores" in e for e in errors)

    def test_level_scores_without_pk_winner_fails(self, r32_seed, valid_predictions):
        preds = copy.deepcopy(valid_predictions)
        preds["FINAL"] = sp(["T01", "T03"], "T01", scores={"T01": 1, "T03": 1})
        errors = validate_bracket(preds, r32_seed)
        assert any("FINAL" in e and "pk_winner" in e for e in errors)

    def test_pk_winner_mismatch_fails(self, r32_seed, valid_predictions):
        preds = copy.deepcopy(valid_predictions)
        # winner is T03 but pk_winner is T29
        preds["SF-2"] = sp(
            ["T03", "T29"],
            "T03",
            scores={"T03": 0, "T29": 0},
            pk_winner="T29",
            pk_scores={"T03": 2, "T29": 3},
        )
        errors = validate_bracket(preds, r32_seed)
        assert any("SF-2" in e and "pk_winner must equal winner" in e for e in errors)

    def test_pk_winner_must_have_higher_pk_score(self, r32_seed, valid_predictions):
        preds = copy.deepcopy(valid_predictions)
        preds["FINAL"] = sp(
            ["T01", "T03"],
            "T01",
            scores={"T01": 1, "T03": 1},
            pk_winner="T01",
            pk_scores={"T01": 3, "T03": 3},
        )
        errors = validate_bracket(preds, r32_seed)
        assert any("FINAL" in e and "strictly higher pk_score" in e for e in errors)

    def test_pk_present_on_decisive_result_fails(self, r32_seed, valid_predictions):
        preds = copy.deepcopy(valid_predictions)
        preds["SF-1"] = sp(
            ["T01", "T23"],
            "T01",
            scores={"T01": 2, "T23": 1},
            pk_winner="T01",
            pk_scores={"T01": 4, "T23": 2},
        )
        errors = validate_bracket(preds, r32_seed)
        assert any("SF-1" in e and "PK fields must be absent" in e for e in errors)
