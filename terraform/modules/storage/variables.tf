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

variable "valkey_num_cache_clusters" {
  description = "Number of cache clusters (nodes) in the Valkey replication group"
  type        = number
  default     = 1
}

variable "valkey_multi_az" {
  description = "Enable Multi-AZ for the Valkey replication group"
  type        = bool
  default     = false
}

variable "valkey_automatic_failover" {
  description = "Enable automatic failover for the Valkey replication group"
  type        = bool
  default     = false
}

variable "valkey_apply_immediately" {
  description = "Apply changes to the Valkey replication group immediately rather than in the next maintenance window"
  type        = bool
  default     = false
}
