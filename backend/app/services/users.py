from datetime import datetime, timezone

import botocore.exceptions

from app.config import settings
from app.db.dynamo import get_table
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


def ensure_exists(user_id: str, email: str) -> None:
    if user_id in _seen:
        return

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
        logger.info("user_autocreated", user_id=user_id)
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] != "ConditionalCheckFailedException":
            raise
        # Record already exists — swallow and continue.

    _seen.add(user_id)


def get(user_id: str) -> UserRecord | None:
    response = get_table(settings.USERS_TABLE).get_item(
        Key={"user_id": user_id}, ConsistentRead=True
    )
    item = response.get("Item")
    if item is None:
        return None
    return UserRecord(**item)
