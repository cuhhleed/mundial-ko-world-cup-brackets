resource "aws_ses_domain_identity" "main" {
  domain = var.domain_name
}

resource "aws_cognito_user_pool" "main" {
  name = "${var.project_name}-${var.environment}"

  # Guard against accidental `terraform destroy` / forced replacement wiping
  # all user accounts. Intentional teardowns must first flip this to INACTIVE
  # or use `terraform state rm`. The dev teardown script already excludes
  # aws_cognito_* resources from its targeted destroy.
  deletion_protection = "ACTIVE"

  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]

  # Cognito requires PASSWORD to always be an allowed first auth factor; it
  # cannot be removed from the pool-level list. Passwordless is still enforced
  # by the app client, which enables only ALLOW_USER_AUTH (no password/SRP
  # flows) — and users are never issued a password.
  sign_in_policy {
    allowed_first_auth_factors = ["PASSWORD", "EMAIL_OTP"]
  }

  mfa_configuration = "OFF"

  email_configuration {
    email_sending_account = "DEVELOPER"
    source_arn            = aws_ses_domain_identity.main.arn
    from_email_address    = "Mundial KO <noreply@${var.domain_name}>"
  }

  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }

  user_attribute_update_settings {
    attributes_require_verification_before_update = ["email"]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-user-pool"
  }
}

resource "aws_cognito_user_pool_client" "frontend" {
  name         = "${var.project_name}-${var.environment}-frontend"
  user_pool_id = aws_cognito_user_pool.main.id

  generate_secret = false

  explicit_auth_flows = [
    "ALLOW_USER_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
  ]

  prevent_user_existence_errors = "ENABLED"

  # Allow refresh tokens to be revoked server-side (e.g. after credential
  # compromise) instead of staying valid for the full 30-day window.
  enable_token_revocation = true

  access_token_validity  = 1
  id_token_validity      = 1
  refresh_token_validity = 30

  token_validity_units {
    access_token  = "hours"
    id_token      = "hours"
    refresh_token = "days"
  }
}
