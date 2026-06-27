variable "region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment name"
  type        = string
  default     = "prod"
}

variable "project_name" {
  description = "Project name used for resource naming and tagging"
  type        = string
  default     = "mundial-ko"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.1.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for the two public subnets"
  type        = list(string)
  default     = ["10.1.1.0/24", "10.1.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for the two private subnets"
  type        = list(string)
  default     = ["10.1.10.0/24", "10.1.11.0/24"]
}

variable "container_port" {
  description = "Port the ECS container listens on"
  type        = number
  default     = 8000
}

variable "domain_name" {
  description = "Root domain name for the project"
  type        = string
  default     = "mundialko.com"
}

variable "api_subdomain" {
  description = "Subdomain prefix for the API endpoint"
  type        = string
  default     = "api"
}

# Non-secret public identifier (ships in the SPA). Console-managed (ADR-004):
# the OAuth client and its authorized origins live in the Google Cloud Console,
# not Terraform — keep the live origins in sync with the frontend URL by hand.
# Shared across dev and prod for now.
variable "google_client_id" {
  description = "Google OAuth client ID (token audience), injected into the API env and the SPA build"
  type        = string
  default     = "525656224688-cbte42k40e6kuk6s2cvq3t2sq2lg8cmt.apps.googleusercontent.com"
}

variable "alert_email" {
  description = "Email address for ingestion alarm notifications"
  type        = string
  default     = "cuhhleed.dev@gmail.com"
}
