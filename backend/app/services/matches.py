from boto3.dynamodb.conditions import Attr

from app.config import settings
from app.db.cache import get_match_state
from app.db.dynamo import get_table
from app.logging import get_logger
from app.models.match import Match

logger = get_logger("matches")


def get_completed_matches() -> dict[str, Match]:
    table = get_table(settings.MATCHES_TABLE)
    items: list[dict] = []
    kwargs: dict = {"FilterExpression": Attr("status").eq("completed")}

    while True:
        response = table.scan(**kwargs)
        items.extend(response.get("Items", []))
        last = response.get("LastEvaluatedKey")
        if last is None:
            break
        kwargs["ExclusiveStartKey"] = last

    return {item["match_id"]: Match(**item) for item in items}


def get_all_matches() -> dict[str, Match]:
    table = get_table(settings.MATCHES_TABLE)
    items: list[dict] = []
    kwargs: dict = {}

    while True:
        response = table.scan(**kwargs)
        items.extend(response.get("Items", []))
        last = response.get("LastEvaluatedKey")
        if last is None:
            break
        kwargs["ExclusiveStartKey"] = last

    return {item["match_id"]: Match(**item) for item in items}


def put_match(match: Match) -> None:
    table = get_table(settings.MATCHES_TABLE)
    table.put_item(Item=match.model_dump(exclude_none=True))


def get_scheduled_matches() -> dict[str, Match]:
    table = get_table(settings.MATCHES_TABLE)
    items: list[dict] = []
    kwargs: dict = {"FilterExpression": Attr("status").eq("scheduled")}

    while True:
        response = table.scan(**kwargs)
        items.extend(response.get("Items", []))
        last = response.get("LastEvaluatedKey")
        if last is None:
            break
        kwargs["ExclusiveStartKey"] = last

    return {item["match_id"]: Match(**item) for item in items}


async def get_all_matches_with_live_overlay() -> dict[str, Match]:
    """Return all matches, overlaying Redis live state for non-completed matches."""
    matches = get_all_matches()

    for match_id, match in list(matches.items()):
        if match.status != "completed":
            redis_data = await get_match_state(match_id)
            if redis_data:
                # Merge Redis fields onto the base match
                merged = {**match.model_dump(), **redis_data}
                # Coerce numeric fields back to int | None
                for field in (
                    "home_score",
                    "away_score",
                    "pk_home_score",
                    "pk_away_score",
                    "match_number",
                ):
                    raw = merged.get(field)
                    if raw is not None and raw != "None":
                        try:
                            merged[field] = int(raw)
                        except (ValueError, TypeError):
                            merged[field] = None
                    else:
                        merged[field] = None
                matches[match_id] = Match(**merged)

    return matches


async def get_match_by_id(match_id: str) -> Match | None:
    """Return a single match, preferring Redis state over DynamoDB."""
    redis_data = await get_match_state(match_id)
    if redis_data:
        # Coerce numeric fields
        coerced: dict = dict(redis_data)
        for field in (
            "home_score",
            "away_score",
            "pk_home_score",
            "pk_away_score",
            "match_number",
        ):
            raw = coerced.get(field)
            if raw is not None and raw != "None":
                try:
                    coerced[field] = int(raw)
                except (ValueError, TypeError):
                    coerced[field] = None
            else:
                coerced[field] = None
        try:
            return Match(**coerced)
        except Exception:
            logger.warning("redis_match_parse_failed", match_id=match_id)

    # Fall back to DynamoDB
    table = get_table(settings.MATCHES_TABLE)
    response = table.get_item(Key={"match_id": match_id})
    item = response.get("Item")
    if item is None:
        return None
    return Match(**item)
