# Architecture Decision Records

This file logs significant architecture decisions for Mundial KO. Each record
captures the context, the decision, and its consequences at the time it was
made. ADRs are append-only history — supersede rather than rewrite them.

---

## ADR-001: Passwordless email OTP for authentication

- **Status:** Accepted
- **Date:** 2026-06-15
- **Sprint:** E1-S6 (Auth infrastructure)

### Context

The original plan called for Cognito with Google OAuth (hosted-UI redirect
flow). That approach carries several costs that are disproportionate for this
project:

- A Google OAuth client must be registered and go through Google's verification
  process, and the client secret must be managed.
- It requires a Cognito hosted UI + custom domain, pulling in DNS and branding
  work we'd rather avoid.
- It ties sign-in to a third-party identity provider.

Cognito's native `USER_AUTH` flow with `EMAIL_OTP` (GA since late 2024) lets a
user authenticate with just an email and a 6-digit code, with no passwords, no
third-party provider, and no client secret.

### Decision

Authenticate users with **passwordless email OTP** via Cognito:

- User pool configured with `sign_in_policy.allowed_first_auth_factors = ["EMAIL_OTP"]`,
  `username_attributes = ["email"]`, `auto_verified_attributes = ["email"]`,
  and `mfa_configuration = "OFF"` (the OTP is already a one-time factor).
- App client is a public SPA client (`generate_secret = false`) with only
  `ALLOW_USER_AUTH` and `ALLOW_REFRESH_TOKEN_AUTH` enabled — no password or SRP
  flows. The React SPA calls `InitiateAuth` → `RespondToAuthChallenge` directly
  against the Cognito public API; **no hosted UI / Cognito domain is needed**.
- Email delivery uses Cognito's default sender (50/day) for now; upgrade to SES
  if the limit becomes a constraint.
- Token validity: access/ID = 1 hour, refresh = 30 days (covers the tournament
  window).

Hardening decisions made alongside the core choice:

- `deletion_protection = "ACTIVE"` on the user pool — guards against an
  accidental `terraform destroy` or forced replacement wiping all accounts. The
  dev teardown script also excludes `aws_cognito_*` from its targeted destroy.
- `enable_token_revocation = true` on the app client — lets a stolen refresh
  token be revoked server-side instead of staying valid for the full 30-day
  window.
- The three compute auth variables (`jwt_issuer`, `cognito_user_pool_id`,
  `cognito_app_client_id`) are **required** (no `""` defaults), so a future
  environment that forgets to wire auth fails at `terraform plan` rather than
  deploying a silently broken service.

### Consequences

**Positive**

- No Google dependency, no OAuth client registration/verification, no client
  secret, no hosted UI or extra DNS.
- Custom login UI lives entirely in the React app (E2-S4), giving full control
  over UX.
- Lower-friction sign-in: email + code, no password to manage or reset.

**Negative / constraints**

- Passwordless-only is a hard constraint: adding password login later requires a
  (destructive) app-client change. `username_attributes` is immutable — getting
  the pool config wrong means destroy + recreate.
- Cognito's 50 email/day default sender limit will throttle heavy test sessions
  until SES is wired up.
- The whole flow depends on reliable email delivery; the only account-recovery
  mechanism configured is `verified_email`.

**Impacts on other work**

- **E2-S4 (frontend login):** Acceptance criteria still describe the old
  Google hosted-UI redirect flow and must be rewritten to the OTP flow. The SPA
  needs `region`, `cognito_user_pool_id`, and `cognito_app_client_id` to
  initialize the Cognito SDK; these are exposed as root Terraform outputs
  (`aws_region`, `cognito_user_pool_id`, `cognito_app_client_id`) on both dev
  and prod and injected at build time as `VITE_*` env vars (Option A — see the
  E2-S4 note in the project plan).
- **E2-S2 (backend JWT middleware):** validates tokens against `JWT_ISSUER`
  (`https://cognito-idp.{region}.amazonaws.com/{pool_id}`) and the app client ID
  (`aud` claim). Config fields are stubbed in `backend/app/config.py`.
- **Deferred:** No `cognito-idp` permissions were added to the ECS task role. JWT
  validation needs none; admin API calls (e.g. `AdminGetUser`) would require
  them. Revisit if/when the backend needs server-side Cognito calls. The
  `user_pool_arn` output is retained for that future IAM scoping.
