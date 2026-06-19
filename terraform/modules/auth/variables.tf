variable "project_name" {
  description = "Project name used for resource naming and tagging"
  type        = string
}

variable "environment" {
  description = "Deployment environment name"
  type        = string
}

variable "domain_name" {
  description = "The domain name used for SES identity and Cognito email sender"
  type        = string
}
