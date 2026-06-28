# Storage module — DynamoDB + ElastiCache Redis (E1-S2, E1-S3)

# ---------------------------------------------------------------------------
# ElastiCache Valkey
# ---------------------------------------------------------------------------

resource "aws_elasticache_subnet_group" "valkey" {
  name       = "${var.project_name}-${var.environment}-valkey"
  subnet_ids = var.private_subnet_ids
}

resource "aws_elasticache_parameter_group" "valkey" {
  name   = "${var.project_name}-${var.environment}-valkey9"
  family = "valkey9"
}

resource "aws_elasticache_replication_group" "valkey" {
  replication_group_id       = "${var.project_name}-${var.environment}-valkey"
  description                = "Valkey cache for ${var.project_name} ${var.environment}"
  engine                     = "valkey"
  engine_version             = "9.0"
  node_type                  = var.valkey_node_type
  num_cache_clusters         = var.valkey_num_cache_clusters
  automatic_failover_enabled = var.valkey_automatic_failover
  multi_az_enabled           = var.valkey_multi_az
  apply_immediately          = var.valkey_apply_immediately
  parameter_group_name       = aws_elasticache_parameter_group.valkey.name
  subnet_group_name          = aws_elasticache_subnet_group.valkey.name
  port                       = 6379
  security_group_ids         = [var.elasticache_security_group_id]
}

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
