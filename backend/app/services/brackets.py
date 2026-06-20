from datetime import datetime, timezone
from uuid import uuid4

import botocore.exceptions

from app.bracket.derivation import validate_bracket
from app.bracket.r32_matchups import load_r32_matchups
from app.config import settings
from app.db.dynamo import get_table
from app.logging import get_logger
from app.models.bracket import Bracket, SlotPrediction

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

    errors = validate_bracket(predictions, r32_matchups)
    if errors:
        raise BracketValidationError(errors)

    bracket_id = str(uuid4())
    created_at = datetime.now(timezone.utc).isoformat()

    serialized_predictions = {
        slot: pred.model_dump(exclude_none=True)
        for slot, pred in predictions.items()
    }

    get_table(settings.BRACKETS_TABLE).put_item(
        Item={
            "bracket_id": bracket_id,
            "user_id": user_id,
            "predictions": serialized_predictions,
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
        predictions=predictions,
        total_points=0,
        status="submitted",
        created_at=created_at,
    )
