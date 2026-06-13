# Storage module — DynamoDB + ElastiCache Redis (E1-S2, E1-S3)

# ---------------------------------------------------------------------------
# Users table
# ---------------------------------------------------------------------------

resource "aws_dynamodb_table" "users" {
  name         = "${var.project_name}-${var.environment}-users"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "user_id"

  attribute {
    name = "user_id"
    type = "S"
  }
}

# ---------------------------------------------------------------------------
# Brackets table
# ---------------------------------------------------------------------------

resource "aws_dynamodb_table" "brackets" {
  name         = "${var.project_name}-${var.environment}-brackets"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "bracket_id"

  attribute {
    name = "bracket_id"
    type = "S"
  }

  attribute {
    name = "user_id"
    type = "S"
  }

  global_secondary_index {
    name            = "user_id-index"
    hash_key        = "user_id"
    projection_type = "ALL"
  }
}

# ---------------------------------------------------------------------------
# Matches table
# ---------------------------------------------------------------------------

resource "aws_dynamodb_table" "matches" {
  name         = "${var.project_name}-${var.environment}-matches"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "match_id"

  attribute {
    name = "match_id"
    type = "S"
  }

  attribute {
    name = "round"
    type = "S"
  }

  global_secondary_index {
    name            = "round-index"
    hash_key        = "round"
    projection_type = "ALL"
  }
}
