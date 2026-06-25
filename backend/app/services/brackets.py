from datetime import datetime, timezone
from uuid import uuid4

import botocore.exceptions

from app.bracket.derivation import validate_bracket
from app.bracket.merge import MergePredictionsError, merge_predictions, slot_prediction_from_match
from app.bracket.r32_matchups import load_r32_matchups
from app.bracket.scoring import score_bracket, score_slot
from app.bracket.topology import ALL_SLOTS, FEEDERS
from app.config import settings
from app.db.dynamo import get_table
from app.logging import get_logger
from app.models.bracket import (
    Bracket,
    BracketResponse,
    BracketTemplate,
    SlotDetail,
    SlotPrediction,
    SlotTemplate,
)
from app.services.matches import get_all_matches, get_completed_matches

logger = get_logger("brackets")


class BracketValidationError(Exception):
    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__(str(errors))


class DuplicateBracketError(Exception):
    pass


def create_bracket(
    user_id: str,
    predictions: dict[str, SlotPrediction],
) -> Bracket:
    r32_matchups = load_r32_matchups()
    completed_matches = get_completed_matches()

    if completed_matches:
        try:
            merged_predictions, locked_slots = merge_predictions(predictions, completed_matches)
        except MergePredictionsError as e:
            raise BracketValidationError(e.errors)
    else:
        merged_predictions = predictions
        locked_slots = []

    errors = validate_bracket(merged_predictions, r32_matchups)
    if errors:
        raise BracketValidationError(errors)

    bracket_id = str(uuid4())
    created_at = datetime.now(timezone.utc).isoformat()

    serialized_predictions = {
        slot: pred.model_dump(exclude_none=True)
        for slot, pred in merged_predictions.items()
    }

    get_table(settings.BRACKETS_TABLE).put_item(
        Item={
            "bracket_id": bracket_id,
            "user_id": user_id,
            "predictions": serialized_predictions,
            "locked_slots": locked_slots,
            "total_points": 0,
            "status": "submitted",
            "created_at": created_at,
        }
    )

    try:
        get_table(settings.USERS_TABLE).update_item(
            Key={"user_id": user_id},
            UpdateExpression="SET bracket_id = :bid",
            ConditionExpression=(
                "attribute_not_exists(bracket_id) OR bracket_id = :null"
            ),
            ExpressionAttributeValues={":bid": bracket_id, ":null": None},
        )
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise DuplicateBracketError()
        raise

    logger.info("bracket_created", bracket_id=bracket_id, user_id=user_id)

    return Bracket(
        bracket_id=bracket_id,
        user_id=user_id,
        predictions=merged_predictions,
        locked_slots=locked_slots,
        total_points=0,
        status="submitted",
        created_at=created_at,
    )


def get_bracket(bracket_id: str) -> Bracket | None:
    response = get_table(settings.BRACKETS_TABLE).get_item(Key={"bracket_id": bracket_id})
    item = response.get("Item")
    if item is None:
        return None
    item["predictions"] = {k: SlotPrediction(**v) for k, v in item["predictions"].items()}
    return Bracket(**item)


def get_all_brackets() -> list[Bracket]:
    table = get_table(settings.BRACKETS_TABLE)
    items: list[dict] = []
    kwargs: dict = {}

    while True:
        response = table.scan(**kwargs)
        items.extend(response.get("Items", []))
        last = response.get("LastEvaluatedKey")
        if last is None:
            break
        kwargs["ExclusiveStartKey"] = last

    brackets = []
    for item in items:
        item["predictions"] = {k: SlotPrediction(**v) for k, v in item["predictions"].items()}
        brackets.append(Bracket(**item))
    return brackets


def rescore_all_brackets() -> dict:
    brackets = get_all_brackets()
    completed_matches = get_completed_matches()

    scored_count = 0
    failed_count = 0
    errors: list[str] = []
    updates: list[tuple] = []

    for bracket in brackets:
        try:
            _, total_points = score_bracket(bracket.predictions, completed_matches, bracket.locked_slots)
            get_table(settings.BRACKETS_TABLE).update_item(
                Key={"bracket_id": bracket.bracket_id},
                UpdateExpression="SET total_points = :pts",
                ExpressionAttributeValues={":pts": total_points},
            )
            updates.append((bracket.bracket_id, bracket.user_id, total_points))
            scored_count += 1
        except Exception as exc:
            msg = f"{bracket.bracket_id}: {exc}"
            logger.error("rescore_bracket_failed", bracket_id=bracket.bracket_id, error=str(exc))
            errors.append(msg)
            failed_count += 1

    return {"scored": scored_count, "failed": failed_count, "errors": errors, "updates": updates}


def build_bracket_response(bracket: Bracket) -> BracketResponse:
    completed_matches = get_completed_matches()
    slots: dict[str, SlotDetail] = {}
    total_points = 0
    for slot_id, prediction in bracket.predictions.items():
        match = completed_matches.get(slot_id)
        result = slot_prediction_from_match(slot_id, match) if match else None
        slot_score = score_slot(slot_id, prediction, result, bracket.locked_slots)
        points = slot_score.total if slot_score.scored else None
        if slot_score.scored:
            total_points += slot_score.total
        slots[slot_id] = SlotDetail(prediction=prediction, result=result, points=points)
    return BracketResponse(
        bracket_id=bracket.bracket_id,
        user_id=bracket.user_id,
        slots=slots,
        locked_slots=bracket.locked_slots,
        total_points=total_points,
        status=bracket.status,
        created_at=bracket.created_at,
    )


def _get_outcome_team(template: SlotTemplate, outcome: str) -> str | None:
    """Return winner or loser team name from a locked slot's result."""
    if not template.result or not template.result.teams:
        return None
    if outcome == "winner":
        return template.result.winner
    return next((t for t in template.result.teams if t != template.result.winner), None)


def get_bracket_template() -> BracketTemplate:
    all_matches = get_all_matches()
    slots: dict[str, SlotTemplate] = {}

    for slot in ALL_SLOTS:
        match = all_matches.get(slot)
        if match and match.status == "completed":
            result = slot_prediction_from_match(slot, match)
            slots[slot] = SlotTemplate(
                slot_id=slot,
                teams=[match.home_team, match.away_team],
                status="locked",
                result=result,
            )
        elif match:
            slots[slot] = SlotTemplate(
                slot_id=slot,
                teams=[match.home_team, match.away_team],
                status="open",
            )
        else:
            slots[slot] = SlotTemplate(
                slot_id=slot,
                teams=None,
                status="open",
            )

    # Derive teams for downstream slots whose both feeders are locked.
    # ALL_SLOTS is in topological order so feeders are always populated first.
    for slot in ALL_SLOTS:
        if slot not in FEEDERS:
            continue
        if slots[slot].teams is not None:
            continue

        (feeder1_id, outcome1), (feeder2_id, outcome2) = FEEDERS[slot]
        f1 = slots.get(feeder1_id)
        f2 = slots.get(feeder2_id)

        if not (f1 and f1.status == "locked" and f2 and f2.status == "locked"):
            continue

        team1 = _get_outcome_team(f1, outcome1)
        team2 = _get_outcome_team(f2, outcome2)

        if team1 and team2:
            slots[slot] = SlotTemplate(
                slot_id=slot,
                teams=[team1, team2],
                status="open",
            )

    return BracketTemplate(slots=slots)
