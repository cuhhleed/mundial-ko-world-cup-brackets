from app.models.bracket import SlotPrediction
from app.bracket.topology import ALL_SLOTS, FEEDERS, SCORE_BEARING_SLOTS


def predicted_loser(slot: str, predictions: dict[str, SlotPrediction]) -> str | None:
    pred = predictions.get(slot)
    if pred is None:
        return None
    for t in pred.teams:
        if t != pred.winner:
            return t
    return None


def derive_matchup(
    slot: str,
    predictions: dict[str, SlotPrediction],
    r32_matchups: dict[str, tuple[str, str]],
) -> tuple[str, str] | None:
    if slot.startswith("R32-"):
        return r32_matchups.get(slot)

    feeders = FEEDERS[slot]
    teams: list[str] = []
    for feeder_slot, outcome in feeders:
        pred = predictions.get(feeder_slot)
        if pred is None:
            return None
        if outcome == "winner":
            teams.append(pred.winner)
        else:
            loser = predicted_loser(feeder_slot, predictions)
            if loser is None:
                return None
            teams.append(loser)
    return (teams[0], teams[1])


def derive_all_matchups(
    predictions: dict[str, SlotPrediction],
    r32_matchups: dict[str, tuple[str, str]],
) -> dict[str, tuple[str, str] | None]:
    return {slot: derive_matchup(slot, predictions, r32_matchups) for slot in ALL_SLOTS}


def validate_bracket(
    predictions: dict[str, SlotPrediction],
    r32_matchups: dict[str, tuple[str, str]],
) -> list[str]:
    errors: list[str] = []

    missing = [s for s in ALL_SLOTS if s not in predictions]
    if missing:
        errors.append(f"Missing slots: {missing}")
        return errors

    for slot in ALL_SLOTS:
        pred = predictions[slot]

        auth_teams = derive_matchup(slot, predictions, r32_matchups)
        if auth_teams is None:
            errors.append(f"{slot}: cannot derive matchup (upstream unpredicted)")
            continue

        if set(pred.teams) != set(auth_teams):
            errors.append(
                f"{slot}: teams {pred.teams} do not match derived matchup {list(auth_teams)}"
            )

        if len(set(pred.teams)) != 2:
            errors.append(f"{slot}: teams must be two distinct teams")

        if pred.winner not in pred.teams:
            errors.append(f"{slot}: winner {pred.winner!r} not in teams {pred.teams}")

        if slot in SCORE_BEARING_SLOTS:
            _validate_score_bearing(slot, pred, errors)
        else:
            if pred.scores is not None:
                errors.append(f"{slot}: winner-only slot must not have scores")
            if pred.pk_winner is not None:
                errors.append(f"{slot}: winner-only slot must not have pk_winner")
            if pred.pk_scores is not None:
                errors.append(f"{slot}: winner-only slot must not have pk_scores")

    return errors


def _validate_score_bearing(slot: str, pred: SlotPrediction, errors: list[str]) -> None:
    if pred.scores is None:
        errors.append(f"{slot}: score-bearing slot requires scores")
        return

    if set(pred.scores.keys()) != set(pred.teams):
        errors.append(f"{slot}: scores must be keyed exactly by teams")

    if any(v < 0 for v in pred.scores.values()):
        errors.append(f"{slot}: scores must be non-negative")

    if pred.winner not in pred.teams:
        return  # winner error already reported by caller

    w_score = pred.scores.get(pred.winner)
    opponent = next((t for t in pred.teams if t != pred.winner), None)
    o_score = pred.scores.get(opponent) if opponent else None

    if w_score is None or o_score is None:
        return  # scores-keyed error already reported

    if w_score > o_score:
        if pred.pk_winner is not None or pred.pk_scores is not None:
            errors.append(f"{slot}: PK fields must be absent for a decisive result")
    elif w_score == o_score:
        if pred.pk_winner is None:
            errors.append(f"{slot}: level 90-min scores require pk_winner")
        else:
            if pred.pk_winner not in pred.teams:
                errors.append(f"{slot}: pk_winner {pred.pk_winner!r} not in teams")
            if pred.pk_winner != pred.winner:
                errors.append(f"{slot}: pk_winner must equal winner when scores are level")
            if pred.pk_scores is None:
                errors.append(f"{slot}: pk_winner requires pk_scores")
            else:
                if set(pred.pk_scores.keys()) != set(pred.teams):
                    errors.append(f"{slot}: pk_scores must be keyed exactly by teams")
                if any(v < 0 for v in pred.pk_scores.values()):
                    errors.append(f"{slot}: pk_scores must be non-negative")
                pk_w = pred.pk_scores.get(pred.pk_winner)
                pk_opp_entry = next(
                    (v for k, v in pred.pk_scores.items() if k != pred.pk_winner), None
                )
                if pk_w is not None and pk_opp_entry is not None and pk_w <= pk_opp_entry:
                    errors.append(f"{slot}: pk_winner must have strictly higher pk_score")
    else:
        errors.append(f"{slot}: winner {pred.winner!r} has lower score than opponent")
