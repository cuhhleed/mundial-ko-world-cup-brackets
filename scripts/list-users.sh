#!/bin/bash
set -euo pipefail

# Lists all registered users from DynamoDB.
#
# Usage:
#   ./scripts/list-users.sh          # targets local DynamoDB (default)
#   ./scripts/list-users.sh dev      # targets dev tables in AWS
#   ./scripts/list-users.sh prod     # targets prod tables in AWS

ENV="${1:-local}"
PROJECT_NAME="${PROJECT_NAME:-mundial-ko}"
TABLE="${PROJECT_NAME}-${ENV}-users"

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

echo "==> Listing users from $TABLE ($ENV)"
echo ""

RESULT=$(aws dynamodb scan \
  --table-name "$TABLE" \
  "${AWS_ARGS[@]}" \
  --output json \
)

COUNT=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('Count', 0))")

if [ "$COUNT" -eq 0 ]; then
  echo "  No users found."
  exit 0
fi

echo "$RESULT" | python3 -c "
import sys, json

data = json.load(sys.stdin)
items = data.get('Items', [])

def val(attr):
    if not attr:
        return '—'
    return next(iter(attr.values()))

print(f'  Found {len(items)} user(s):')
print()
print(f'  {\"USER ID\":<40} {\"DISPLAY NAME\":<25} {\"EMAIL\":<35}')
print(f'  {\"─\" * 40} {\"─\" * 25} {\"─\" * 35}')

for item in sorted(items, key=lambda i: val(i.get('display_name', {})).lower()):
    uid = val(item.get('user_id', {}))
    name = val(item.get('display_name', {}))
    email = val(item.get('email', {}))
    print(f'  {uid:<40} {name:<25} {email:<35}')
"

echo ""
echo "==> $COUNT user(s) total."
