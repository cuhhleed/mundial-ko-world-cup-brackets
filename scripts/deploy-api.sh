#!/bin/bash
set -euo pipefail

# Builds the backend Docker image, pushes it to ECR (tagged :latest and :<git-sha>),
# and triggers a force-new-deployment on the ECS service.
#
# Usage: ./scripts/deploy-api.sh [dev|prod]

ENV="${1:-dev}"
[[ "$ENV" == "dev" || "$ENV" == "prod" ]] || { echo "Usage: $0 [dev|prod]"; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$SCRIPT_DIR/.."
INFRA_DIR="$REPO_ROOT/terraform/environments/$ENV"

tf_output() {
  terraform -chdir="$INFRA_DIR" output -raw "$1" 2>/dev/null || {
    echo "ERROR: failed to read Terraform output '$1'."
    echo "       Run 'terraform init && terraform apply' in $INFRA_DIR first."
    exit 1
  }
}

echo "==> Environment: $ENV"
echo "==> Reading Terraform outputs from $INFRA_DIR"

ECR_URL="$(tf_output ecr_repository_url)"
CLUSTER="$(tf_output ecs_cluster_name)"
SERVICE="$(tf_output ecs_service_name)"
REGION="$(tf_output aws_region)"

GIT_SHA="$(git rev-parse --short HEAD)"

TAG_LATEST="$ECR_URL:latest"
TAG_SHA="$ECR_URL:$GIT_SHA"

ECR_REGISTRY="${ECR_URL%%/*}"

echo "==> Authenticating Docker with ECR ($ECR_REGISTRY)"
aws ecr get-login-password --region "$REGION" \
  | docker login --username AWS --password-stdin "$ECR_REGISTRY"

echo "==> Building image (platform: linux/amd64)"
docker build \
  --platform linux/amd64 \
  --tag "$TAG_LATEST" \
  --tag "$TAG_SHA" \
  "$REPO_ROOT/backend"

echo "==> Pushing $TAG_LATEST"
docker push "$TAG_LATEST"

echo "==> Pushing $TAG_SHA"
docker push "$TAG_SHA"

echo "==> Triggering ECS force-new-deployment (cluster=$CLUSTER, service=$SERVICE)"
aws ecs update-service \
  --cluster "$CLUSTER" \
  --service "$SERVICE" \
  --force-new-deployment \
  --region "$REGION" \
  >/dev/null

API_URL="$(tf_output api_url)"

echo ""
echo "==> Deploy triggered successfully."
echo "    Pushed tags : $TAG_LATEST"
echo "                  $TAG_SHA"
echo "    API URL     : $API_URL"
echo ""
echo "    TIP: to block until the rollout settles, run:"
echo "      aws ecs wait services-stable --cluster $CLUSTER --services $SERVICE --region $REGION"
