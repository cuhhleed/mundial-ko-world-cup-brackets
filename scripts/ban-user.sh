#!/bin/bash
set -euo pipefail

# Bans a user by deleting their bracket, blocking re-creation and removing
# them from the leaderboard on the next rescore cycle.
#
# The user record is intentionally left intact — its stale bracket_id
# prevents the user from creating a new bracket (DuplicateBracketError),
# and the email uniqueness constraint blocks re-registration.
#
# Usage:
#   ./scripts/ban-user.sh <user_id>          # targets local DynamoDB (default)
#   ./scripts/ban-user.sh <user_id> dev      # targets dev tables in AWS
#   ./scripts/ban-user.sh <user_id> prod     # targets prod tables in AWS

USER_ID="${1:-}"
ENV="${2:-local}"
PROJECT_NAME="${PROJECT_NAME:-mundial-ko}"
USERS_TABLE="${PROJECT_NAME}-${ENV}-users"
BRACKETS_TABLE="${PROJECT_NAME}-${ENV}-brackets"

if [ -z "$USER_ID" ]; then
  echo "Usage: $0 <user_id> [local|dev|prod]" >&2
  exit 1
fi

case "$ENV" in
  local)
    ENDPOINT="http://localhost:8001"
    AWS_ARGS=(--endpoint-url "$ENDPOINT" --region localhost)
    export AWS_ACCESS_KEY_ID="DUMMYIDEXAMPLE"
    export AWS_SECRET_ACCESS_KEY="DUMMYSECRETANDKEYEXAMPLE"
    ;;
  dev|prod)
    AWS_ARGS=(--region us-east-1)
    ;;
  *)
    echo "Unknown environment: $ENV (use local, dev, or prod)" >&2
    exit 1
    ;;
esac

echo "==> Looking up user $USER_ID in $USERS_TABLE ($ENV)"
echo ""

USER_RESULT=$(aws dynamodb get-item \
  --table-name "$USERS_TABLE" \
  --key "{\"user_id\": {\"S\": \"$USER_ID\"}}" \
  "${AWS_ARGS[@]}" \
  --output json \
)

ITEM=$(echo "$USER_RESULT" | python3 -c "import sys,json; print(json.dumps(json.load(sys.stdin).get('Item')))")

if [ "$ITEM" = "null" ] || [ -z "$ITEM" ]; then
  echo "  User not found: $USER_ID" >&2
  exit 1
fi

echo "$ITEM" | python3 -c "
import sys, json

item = json.load(sys.stdin)

def val(attr):
    if not attr:
        return '—'
    return next(iter(attr.values()))

email = val(item.get('email', {}))
display_name = val(item.get('display_name', {}))
bracket_id = val(item.get('bracket_id', {}))

print(f'  Email:        {email}')
print(f'  Display name: {display_name}')
print(f'  Bracket ID:   {bracket_id}')
"

echo ""
read -rp "  Ban this user? Deletes their bracket. (y/n): " CONFIRM

if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
  echo "  Aborted."
  exit 0
fi

echo ""

BRACKET_ID=$(echo "$ITEM" | python3 -c "
import sys, json
item = json.load(sys.stdin)
attr = item.get('bracket_id', {})
print(next(iter(attr.values())) if attr else '')
")

if [ -z "$BRACKET_ID" ] || [ "$BRACKET_ID" = "—" ]; then
  echo "  No bracket_id on user record — nothing to delete."
else
  echo "==> Deleting bracket $BRACKET_ID from $BRACKETS_TABLE"
  aws dynamodb delete-item \
    --table-name "$BRACKETS_TABLE" \
    --key "{\"bracket_id\": {\"S\": \"$BRACKET_ID\"}}" \
    "${AWS_ARGS[@]}" \
    --output json > /dev/null
  echo "  Bracket deleted."
fi

echo ""
echo "==> Done."
echo "  User record kept intact (stale bracket_id blocks re-creation)."
echo "  User will be removed from leaderboard on the next rescore cycle."
