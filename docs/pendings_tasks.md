# Pending Tasks

Deferred work that is decided but intentionally not yet executed. Each task
records its trigger condition so it isn't actioned prematurely. Remove a task
(or mark it done) once completed.

---

## TASK-001: Retire Cognito + SES infrastructure

- **Status:** Pending
- **Created:** 2026-06-19
- **Related:** ADR-004 (auth pivot to Google Sign-In)
- **Precondition:** Google Sign-In is fully set up and **validated in the live
  app** — i.e. the backend validates Google ID tokens against Google's JWKS and
  the frontend GIS flow works end-to-end in a deployed environment. Do **not**
  start this task until that is confirmed; until then Cognito remains the
  fallback.

### Why

ADR-004 replaces Cognito `EMAIL_OTP` + SES with Google Sign-In. Once Google auth
is proven in the live app, the Cognito user pool, app client, and SES domain
identity are dead infrastructure and should be torn down to remove cost,
attack surface, and config drift.

### Steps

1. Flip the user pool's `deletion_protection` from `ACTIVE` to `INACTIVE` (it
   was set `ACTIVE` in ADR-001 to guard exactly this).
2. Remove the `aws_cognito_*` exclusion from `scripts/dev_tf_teardown.sh`.
3. Remove `aws_cognito_user_pool`, `aws_cognito_user_pool_client`, and
   `aws_ses_domain_identity` from the Terraform `auth` module.
4. Remove the `cognito_user_pool_id` / `cognito_app_client_id` root outputs and
   the corresponding `VITE_COGNITO_*` build/env vars.
5. Remove the now-dead backend config (`JWT_ISSUER`, `COGNITO_USER_POOL_ID`,
   `COGNITO_APP_CLIENT_ID`) if not already replaced under ADR-004.
6. `terraform apply` / destroy and confirm the resources are gone in both dev
   and prod.

### Notes

- Destroying the pool is **irreversible** and discards any accounts in it.
  Acceptable pre-launch (no real users), but confirm before running in prod.
