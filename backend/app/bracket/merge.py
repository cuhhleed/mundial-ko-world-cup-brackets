from app.bracket.topology import ALL_SLOTS, SCORE_BEARING_SLOTS
from app.models.bracket import SlotPrediction
from app.models.match import Match


def slot_prediction_from_match(slot: str, match: Match) -> SlotPrediction:
    home = match.home_team
    away = match.away_team
    teams = [home, away]

    hs = match.home_score
    as_ = match.away_score

    if hs is not None and as_ is not None and hs > as_:
        winner = home
    elif hs is not None and as_ is not None and as_ > hs:
        winner = away
    else:
        winner = match.pk_winner  # type: ignore[assignment]

    if slot in SCORE_BEARING_SLOTS:
        scores = {home: hs, away: as_}
        if hs == as_:
            pk_winner = match.pk_winner
            pk_scores = (
                {home: match.pk_home_score, away: match.pk_away_score}
                if match.pk_home_score is not None and match.pk_away_score is not None
                else None
            )
            return SlotPrediction(
                teams=teams,
                winner=winner,
                scores=scores,
                pk_winner=pk_winner,
                pk_scores=pk_scores,
            )
        return SlotPrediction(teams=teams, winner=winner, scores=scores)

    return SlotPrediction(teams=teams, winner=winner)


def merge_predictions(
    user_predictions: dict[str, SlotPrediction],
    completed_matches: dict[str, Match],
) -> tuple[dict[str, SlotPrediction], list[str]]:
    merged: dict[str, SlotPrediction] = {}
    locked: list[str] = []
    errors: list[str] = []

    for slot in ALL_SLOTS:
        if slot in completed_matches:
            if slot in user_predictions:
                errors.append(
                    f"{slot}: prediction submitted for a locked (completed) slot"
                )
                continue
            merged[slot] = slot_prediction_from_match(slot, completed_matches[slot])
            locked.append(slot)
        else:
            if slot not in user_predictions:
                errors.append(f"{slot}: prediction missing for an open slot")
                continue
            merged[slot] = user_predictions[slot]

    if errors:
        raise MergePredictionsError(errors)

    return merged, locked


class MergePredictionsError(Exception):
    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__(str(errors))
