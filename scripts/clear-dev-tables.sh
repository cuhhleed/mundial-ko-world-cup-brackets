#!/bin/bash
set -euo pipefail

# Clears all items from the DEV DynamoDB tables.
# Hardcoded to dev table names — cannot accidentally hit prod.
#
# Usage: ./scripts/clear-dev-tables.sh

REGION="us-east-1"

TABLES=(
  "mundial-ko-dev-users:user_id"
  "mundial-ko-dev-brackets:bracket_id"
  "mundial-ko-dev-matches:match_id"
)

for entry in "${TABLES[@]}"; do
  TABLE="${entry%%:*}"
  KEY="${entry##*:}"

  echo "==> Scanning $TABLE"
  KEYS=$(aws dynamodb scan \
    --table-name "$TABLE" \
    --projection-expression "#k" \
    --expression-attribute-names "{\"#k\": \"$KEY\"}" \
    --region "$REGION" \
    --output json \
    --query "Items[].{\"$KEY\": $KEY}" \
  )

  COUNT=$(echo "$KEYS" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))")

  if [ "$COUNT" -eq 0 ]; then
    echo "    (empty — nothing to delete)"
    continue
  fi

  echo "    Deleting $COUNT items..."

  echo "$KEYS" | python3 -c "
import sys, json

items = json.load(sys.stdin)
key = '$KEY'

# BatchWriteItem accepts max 25 items per call
for i in range(0, len(items), 25):
    batch = items[i:i+25]
    requests = [{\"DeleteRequest\": {\"Key\": item}} for item in batch]
    payload = {\"$TABLE\": requests}
    json.dump(payload, sys.stdout)
    print()
" | while IFS= read -r batch; do
    aws dynamodb batch-write-item \
      --request-items "$batch" \
      --region "$REGION" \
      >/dev/null
  done

  echo "    Done."
done

echo ""
echo "==> All dev tables cleared."
