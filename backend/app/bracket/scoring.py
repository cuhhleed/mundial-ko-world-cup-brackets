from dataclasses import dataclass

from app.bracket.points import POINTS
from app.models.bracket import SlotPrediction


@dataclass(frozen=True)
class SlotScore:
    scored: bool = False
    winner_points: int = 0
    score_points: int = 0
    pk_score_points: int = 0
    total: int = 0


def _round_for_slot(slot_id: str) -> str:
    """Return the round name for a given slot ID."""
    if slot_id in ("FINAL", "TP"):
        return slot_id
    return slot_id.split("-")[0]


def score_slot(
    slot_id: str,
    prediction: SlotPrediction,
    result: SlotPrediction | None,
    locked_slots: list[str],
) -> SlotScore:
    """Score a single slot prediction against the actual result."""
    if result is None:
        return SlotScore(scored=False)

    if slot_id in locked_slots:
        return SlotScore(scored=True)

    point_values = POINTS[_round_for_slot(slot_id)]

    correct_winner = prediction.winner == result.winner
    correct_score = (
        result.scores is not None
        and prediction.scores is not None
        and prediction.scores == result.scores
    )
    correct_pk = (
        result.pk_scores is not None
        and prediction.pk_scores is not None
        and prediction.pk_scores == result.pk_scores
    )

    winner_points = int(correct_winner) * point_values.correct_winner
    score_points = int(correct_score) * point_values.correct_score
    pk_score_points = int(correct_pk) * point_values.correct_pk_score
    total = winner_points + score_points + pk_score_points

    return SlotScore(
        scored=True,
        winner_points=winner_points,
        score_points=score_points,
        pk_score_points=pk_score_points,
        total=total,
    )


def score_bracket(
    predictions: dict[str, SlotPrediction],
    completed_matches: dict,
    locked_slots: list[str],
) -> tuple[dict[str, int | None], int]:
    """Score all slots in a bracket.

    Returns a dict of slot_id → points (None if match not played, int if scored)
    and the total points across all scored slots.
    """
    from app.bracket.merge import slot_prediction_from_match

    per_slot: dict[str, int | None] = {}
    total = 0

    for slot_id, prediction in predictions.items():
        match = completed_matches.get(slot_id)
        result = slot_prediction_from_match(slot_id, match) if match else None
        slot_score = score_slot(slot_id, prediction, result, locked_slots)

        if slot_score.scored:
            per_slot[slot_id] = slot_score.total
            total += slot_score.total
        else:
            per_slot[slot_id] = None

    return per_slot, total
