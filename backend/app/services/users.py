from datetime import datetime, timezone

import botocore.exceptions

from app.config import settings
from app.db.dynamo import get_dynamodb, get_table
from app.logging import get_logger
from app.models.user import UserRecord
from app.services.usernames import generate_display_name

logger = get_logger("users")

# In-process cache: avoids a DynamoDB round-trip on every request for users we
# have already confirmed exist this process lifetime.
_seen: set[str] = set()


def reset_seen_cache() -> None:
    """Clear the in-process cache. Call this in tests for isolation."""
    _seen.clear()


class UserAlreadyExistsError(Exception):
    pass


def create(user_id: str, email: str) -> UserRecord:
    display_name = generate_display_name()
    created_at = datetime.now(timezone.utc).isoformat()

    try:
        get_table(settings.USERS_TABLE).put_item(
            Item={
                "user_id": user_id,
                "email": email,
                "display_name": display_name,
                "created_at": created_at,
            },
            ConditionExpression="attribute_not_exists(user_id)",
        )
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise UserAlreadyExistsError()
        raise

    _seen.add(user_id)
    logger.info("user_created", user_id=user_id)
    return UserRecord(
        user_id=user_id,
        email=email,
        display_name=display_name,
        created_at=created_at,
    )


def get(user_id: str) -> UserRecord | None:
    response = get_table(settings.USERS_TABLE).get_item(
        Key={"user_id": user_id}, ConsistentRead=True
    )
    item = response.get("Item")
    if item is None:
        return None
    return UserRecord(**item)


def update_display_name(user_id: str, display_name: str) -> UserRecord | None:
    try:
        response = get_table(settings.USERS_TABLE).update_item(
            Key={"user_id": user_id},
            UpdateExpression="SET display_name = :dn",
            ConditionExpression="attribute_exists(user_id)",
            ExpressionAttributeValues={":dn": display_name},
            ReturnValues="ALL_NEW",
        )
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return None
        raise
    return UserRecord(**response["Attributes"])


def batch_get_display_names(user_ids: list[str]) -> dict[str, str]:
    if not user_ids:
        return {}

    result: dict[str, str] = {}
    dynamo = get_dynamodb()

    # Process in chunks of 100 (DynamoDB BatchGetItem limit)
    chunk_size = 100
    for i in range(0, len(user_ids), chunk_size):
        chunk = user_ids[i : i + chunk_size]
        unprocessed: dict = {
            settings.USERS_TABLE: {
                "Keys": [{"user_id": uid} for uid in chunk],
                "ProjectionExpression": "user_id, display_name",
            }
        }

        while unprocessed:
            response = dynamo.batch_get_item(RequestItems=unprocessed)
            items = response.get("Responses", {}).get(settings.USERS_TABLE, [])
            for item in items:
                result[item["user_id"]] = item["display_name"]
            unprocessed = response.get("UnprocessedKeys", {})

    return result
