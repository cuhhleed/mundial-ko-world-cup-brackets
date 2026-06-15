variable "project_name" {
  description = "Project name used for resource naming and tagging"
  type        = string
}

variable "environment" {
  description = "Deployment environment name"
  type        = string
}

variable "domain_name" {
  description = "Root domain name (e.g. mundialko.com)"
  type        = string
}

variable "acm_certificate_arn" {
  description = "ARN of the ACM certificate (must be in us-east-1 for CloudFront)"
  type        = string
}

variable "route53_zone_id" {
  description = "ID of the Route 53 hosted zone for the domain"
  type        = string
}
