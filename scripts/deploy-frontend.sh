#!/bin/bash
set -euo pipefail

# Builds the React/Vite frontend, syncs the dist/ output to S3, and invalidates
# the CloudFront distribution. Cognito config is injected at build time as VITE_*
# env vars read from Terraform outputs.
#
# Usage: ./scripts/deploy-frontend.sh [dev|prod]

ENV="${1:-dev}"
[[ "$ENV" == "dev" || "$ENV" == "prod" ]] || { echo "Usage: $0 [dev|prod]"; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$SCRIPT_DIR/.."
INFRA_DIR="$REPO_ROOT/terraform/environments/$ENV"
FRONTEND_DIR="$REPO_ROOT/frontend"

# Guard: frontend app must exist before this script is useful (added in E2-S3).
if [[ ! -f "$FRONTEND_DIR/package.json" ]]; then
  echo "ERROR: $FRONTEND_DIR/package.json not found."
  echo "       The frontend React app has not been scaffolded yet (E2-S3)."
  echo "       Create the Vite app under frontend/ before running this script."
  exit 1
fi

tf_output() {
  terraform -chdir="$INFRA_DIR" output -raw "$1" 2>/dev/null || {
    echo "ERROR: failed to read Terraform output '$1'."
    echo "       Run 'terraform init && terraform apply' in $INFRA_DIR first."
    exit 1
  }
}

echo "==> Environment: $ENV"
echo "==> Reading Terraform outputs from $INFRA_DIR"

BUCKET="$(tf_output s3_bucket_name)"
DIST_ID="$(tf_output cloudfront_distribution_id)"
REGION="$(tf_output aws_region)"

# ---------------------------------------------------------------------------
# Inject build-time Cognito config as VITE_* env vars.
# These are non-secret public identifiers required by the Cognito SDK.
# ---------------------------------------------------------------------------
VITE_AWS_REGION="$REGION"
VITE_COGNITO_USER_POOL_ID="$(tf_output cognito_user_pool_id)"
VITE_COGNITO_APP_CLIENT_ID="$(tf_output cognito_app_client_id)"
export VITE_AWS_REGION VITE_COGNITO_USER_POOL_ID VITE_COGNITO_APP_CLIENT_ID

echo "==> Injecting Cognito config:"
echo "    VITE_AWS_REGION              = $VITE_AWS_REGION"
echo "    VITE_COGNITO_USER_POOL_ID    = $VITE_COGNITO_USER_POOL_ID"
echo "    VITE_COGNITO_APP_CLIENT_ID   = $VITE_COGNITO_APP_CLIENT_ID"

echo "==> Building frontend (npm ci && npm run build)"
cd "$FRONTEND_DIR"
npm ci
npm run build

# TODO (optimization): replace the single sync below with a two-pass sync that sets
# a long Cache-Control max-age on fingerprinted assets (js/css/img) and no-cache on
# index.html, before running the CloudFront invalidation. This avoids stale asset
# references during the CDN propagation window. Keep the single-pass sync for now
# until the frontend build pipeline is stable.
echo "==> Syncing dist/ to s3://$BUCKET"
aws s3 sync dist/ "s3://$BUCKET" --delete --region "$REGION"

echo "==> Invalidating CloudFront distribution $DIST_ID"
aws cloudfront create-invalidation \
  --distribution-id "$DIST_ID" \
  --paths "/*" \
  >/dev/null

FRONTEND_URL="$(tf_output frontend_url)"

echo ""
echo "==> Deploy complete."
echo "    S3 bucket       : $BUCKET"
echo "    Distribution ID : $DIST_ID"
echo "    Frontend URL    : $FRONTEND_URL"
