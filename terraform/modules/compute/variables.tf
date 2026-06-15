# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------

variable "project_name" {
  description = "Project name used for resource naming and tagging"
  type        = string
}

variable "environment" {
  description = "Deployment environment name"
  type        = string
}

variable "region" {
  description = "AWS region to deploy into"
  type        = string
}

# ---------------------------------------------------------------------------
# Networking inputs (from networking module)
# ---------------------------------------------------------------------------

variable "vpc_id" {
  description = "ID of the VPC"
  type        = string
}

variable "public_subnet_ids" {
  description = "IDs of the public subnets (for ALB)"
  type        = list(string)
}

variable "private_subnet_ids" {
  description = "IDs of the private subnets (for ECS tasks)"
  type        = list(string)
}

variable "alb_security_group_id" {
  description = "Security group ID for the Application Load Balancer"
  type        = string
}

variable "ecs_security_group_id" {
  description = "Security group ID for ECS Fargate tasks"
  type        = string
}

# ---------------------------------------------------------------------------
# Storage inputs (from storage module)
# ---------------------------------------------------------------------------

variable "users_table_name" {
  description = "Name of the Users DynamoDB table"
  type        = string
}

variable "users_table_arn" {
  description = "ARN of the Users DynamoDB table"
  type        = string
}

variable "brackets_table_name" {
  description = "Name of the Brackets DynamoDB table"
  type        = string
}

variable "brackets_table_arn" {
  description = "ARN of the Brackets DynamoDB table"
  type        = string
}

variable "matches_table_name" {
  description = "Name of the Matches DynamoDB table"
  type        = string
}

variable "matches_table_arn" {
  description = "ARN of the Matches DynamoDB table"
  type        = string
}

variable "redis_endpoint" {
  description = "DNS endpoint of the Valkey/Redis cache node"
  type        = string
}

variable "redis_port" {
  description = "Port of the Valkey/Redis cache node"
  type        = number
}

# ---------------------------------------------------------------------------
# Compute config
# ---------------------------------------------------------------------------

variable "container_port" {
  description = "Port the ECS container listens on"
  type        = number
  default     = 8000
}

variable "task_cpu" {
  description = "CPU units for the ECS task (256 = 0.25 vCPU)"
  type        = number
  default     = 256
}

variable "task_memory" {
  description = "Memory (MB) for the ECS task"
  type        = number
  default     = 512
}

variable "desired_count" {
  description = "Desired number of running ECS task instances"
  type        = number
  default     = 1
}

variable "health_check_path" {
  description = "HTTP path for ALB health checks"
  type        = string
  default     = "/health"
}

# ---------------------------------------------------------------------------
# DNS / TLS
# ---------------------------------------------------------------------------

variable "domain_name" {
  description = "Root domain name (hosted zone name)"
  type        = string
  default     = "mundialko.com"
}

variable "api_subdomain" {
  description = "Subdomain prefix for the API endpoint"
  type        = string
  default     = "api"
}

# ---------------------------------------------------------------------------
# Auth (from auth module)
# ---------------------------------------------------------------------------

variable "jwt_issuer" {
  description = "Cognito User Pool issuer URL"
  type        = string
}

variable "cognito_user_pool_id" {
  description = "Cognito User Pool ID"
  type        = string
}

variable "cognito_app_client_id" {
  description = "Cognito app client ID"
  type        = string
}
