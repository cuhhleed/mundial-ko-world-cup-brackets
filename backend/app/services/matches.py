from boto3.dynamodb.conditions import Attr

from app.config import settings
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