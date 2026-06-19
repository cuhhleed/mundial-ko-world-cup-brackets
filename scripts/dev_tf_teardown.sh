#!/bin/bash
set -e

# Destroys all dev Terraform resources EXCEPT those matching KEEP_PATTERNS.
# This is an exclusive approach: any new resource added to the stack will be
# torn down automatically unless explicitly added to the keep list below.
# Free/idle resources (VPC, subnets, IGW, route tables, security groups,
# DynamoDB on-demand, S3, CloudFront, Cognito, ECR) are kept to speed up
# re-spinup and avoid the 20-30 min ENI detachment delay that occurs when
# destroying security groups attached to recently-terminated ENIs.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$SCRIPT_DIR/../terraform/environments/dev"

echo "==> Switching to Terraform environment: $INFRA_DIR"
cd "$INFRA_DIR"

KEEP_PATTERNS=(
  "\.data\."
  "aws_vpc\."
  "aws_subnet\."
  "aws_internet_gateway\."
  "aws_route_table\."
  "aws_route_table_association\."
  "aws_security_group\."
  "aws_vpc_security_group_"
  "aws_dynamodb_table\."
  "aws_dynamodb_table_item\."
  "aws_s3_bucket"
  "aws_cloudfront_"
  "aws_cognito_"
  "aws_ses_"
  "aws_ecr_"
  "aws_iam_"
  "aws_acm_"
  "aws_route53_"
  "aws_cloudwatch_"
)

EXCLUDE=$(printf "|%s" "${KEEP_PATTERNS[@]}")
EXCLUDE="${EXCLUDE:1}"

TARGETS=$(terraform state list 2>/dev/null | grep -vE "$EXCLUDE" || true)

if [ -z "$TARGETS" ]; then
  echo "No expensive resources found to tear down."
  exit 0
fi

TARGET_FLAGS=""
for target in $TARGETS; do
  TARGET_FLAGS="$TARGET_FLAGS -target=$target"
done

echo ""
echo "Resources to be DESTROYED:"
for target in $TARGETS; do
  echo "  $target"
done
echo ""
echo "Resources being KEPT:"
terraform state list 2>/dev/null | grep -E "$EXCLUDE" | while read -r r; do echo "  $r"; done || true
echo ""
read -p "Proceed with destroy? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
  echo "Aborted."
  exit 0
fi

echo "==> Running targeted destroy..."
terraform destroy $TARGET_FLAGS

echo "==> Teardown complete. Run 'terraform apply' to re-spinup."
