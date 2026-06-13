# Storage module variables — DynamoDB + ElastiCache Redis (E1-S2, E1-S3)

variable "project_name" {
  description = "Project name used for resource naming and tagging"
  type        = string
}

variable "environment" {
  description = "Deployment environment (e.g. dev, prod)"
  type        = string
}
