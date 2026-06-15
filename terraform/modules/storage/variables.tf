# Storage module variables — DynamoDB + ElastiCache Redis (E1-S2, E1-S3)

variable "project_name" {
  description = "Project name used for resource naming and tagging"
  type        = string
}

variable "environment" {
  description = "Deployment environment (e.g. dev, prod)"
  type        = string
}

variable "private_subnet_ids" {
  description = "IDs of private subnets for the ElastiCache subnet group"
  type        = list(string)
}

variable "elasticache_security_group_id" {
  description = "Security group ID to attach to the ElastiCache cluster"
  type        = string
}

variable "valkey_node_type" {
  description = "ElastiCache node instance type"
  type        = string
  default     = "cache.t3.micro"
}
