terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  # Bootstrap uses local state intentionally — it creates the remote backend.
  # Do not add a remote backend block here.
}

provider "aws" {
  region = var.region
}

# ---------------------------------------------------------------------------
# S3 — Terraform state bucket
# ---------------------------------------------------------------------------

resource "aws_s3_bucket" "tfstate" {
  bucket = "mundial-ko-tfstate-${var.account_id}"

  lifecycle {
    prevent_destroy = true
  }

  tags = {
    Name      = "mundial-ko-tfstate-${var.account_id}"
    ManagedBy = "terraform-bootstrap"
  }
}

resource "aws_s3_bucket_versioning" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ---------------------------------------------------------------------------
# DynamoDB — Terraform state lock table
# ---------------------------------------------------------------------------

resource "aws_dynamodb_table" "tflock" {
  name         = "mundial-ko-tflock"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = {
    Name      = "mundial-ko-tflock"
    ManagedBy = "terraform-bootstrap"
  }
}
