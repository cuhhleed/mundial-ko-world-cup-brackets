terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # All backend config is supplied at init time via -backend-config=backend.hcl
  backend "s3" {}
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = "mundial-ko"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# ---------------------------------------------------------------------------
# Networking
# ---------------------------------------------------------------------------

module "networking" {
  source = "../../modules/networking"

  project_name         = var.project_name
  environment          = var.environment
  vpc_cidr             = var.vpc_cidr
  public_subnet_cidrs  = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
  container_port       = var.container_port
}

# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

module "storage" {
  source = "../../modules/storage"

  project_name                  = var.project_name
  environment                   = var.environment
  private_subnet_ids            = module.networking.private_subnet_ids
  elasticache_security_group_id = module.networking.elasticache_security_group_id

  valkey_node_type          = var.valkey_node_type
  valkey_num_cache_clusters = var.valkey_num_cache_clusters
  valkey_multi_az           = var.valkey_multi_az
  valkey_automatic_failover = var.valkey_automatic_failover
  valkey_apply_immediately  = var.valkey_apply_immediately
}

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

module "auth" {
  source = "../../modules/auth"

  project_name = var.project_name
  environment  = var.environment
  domain_name  = var.domain_name
}

# ---------------------------------------------------------------------------
# Compute
# ---------------------------------------------------------------------------

module "compute" {
  source = "../../modules/compute"

  project_name = var.project_name
  environment  = var.environment
  region       = var.region

  vpc_id                = module.networking.vpc_id
  public_subnet_ids     = module.networking.public_subnet_ids
  private_subnet_ids    = module.networking.private_subnet_ids
  alb_security_group_id = module.networking.alb_security_group_id
  ecs_security_group_id = module.networking.ecs_security_group_id

  users_table_name    = module.storage.users_table_name
  users_table_arn     = module.storage.users_table_arn
  brackets_table_name = module.storage.brackets_table_name
  brackets_table_arn  = module.storage.brackets_table_arn
  matches_table_name  = module.storage.matches_table_name
  matches_table_arn   = module.storage.matches_table_arn
  redis_endpoint      = module.storage.redis_endpoint
  redis_port          = module.storage.redis_port

  domain_name   = var.domain_name
  api_subdomain = var.api_subdomain

  jwt_issuer            = module.auth.jwt_issuer_url
  cognito_user_pool_id  = module.auth.user_pool_id
  cognito_app_client_id = module.auth.app_client_id
  google_client_id      = var.google_client_id

  alert_email   = var.alert_email
  desired_count = var.desired_count
}

# ---------------------------------------------------------------------------
# Frontend
# ---------------------------------------------------------------------------

module "frontend" {
  source = "../../modules/frontend"

  project_name        = var.project_name
  environment         = var.environment
  domain_name         = var.domain_name
  acm_certificate_arn = module.compute.acm_certificate_arn
  route53_zone_id     = module.compute.route53_zone_id
}
