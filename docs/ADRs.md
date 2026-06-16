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

- User pool configured with `sign_in_policy.allowed_first_auth_factors =
  ["PASSWORD", "EMAIL_OTP"]`, `username_attributes = ["email"]`,
  `auto_verified_attributes = ["email"]`, and `mfa_configuration = "OFF"` (the
  OTP is already a one-time factor). Cognito requires `PASSWORD` in the
  pool-level factor list and rejects pools that omit it; passwordless is
  enforced one level down by the app client (see below), and no user is ever
  issued a password.
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

---

## ADR-002: Cognito JWT validation strategy, display_name ownership, and auth dependency model

- **Status:** Accepted
- **Date:** 2026-06-15
- **Sprint:** E2-S2 (Cognito JWT validation)

### Context

With the Cognito user pool in place (ADR-001), the backend needs to validate
incoming bearer tokens, derive a user identity, and ensure a user record exists
in DynamoDB before serving protected responses. Three design questions arose:

1. **Which Cognito token to validate?** Cognito issues both an ID token (carrying
   `email`, `name`, and other profile claims) and an access token (carrying only
   `sub` and scopes). The backend needs `email` to bootstrap the user record, and
   only the ID token carries it. The ID token also carries `token_use = "id"`,
   which lets the verifier explicitly reject misuse of the access token.

2. **Who owns `display_name`?** The Cognito token does not contain a
   display_name. The project design calls for a randomized football handle
   (e.g. `NutmegMaestro10`) rather than a name derived from the user's email or
   identity provider profile. Deriving a name from email would expose PII in
   a public leaderboard.

3. **How should auth be enforced?** The app has public endpoints (leaderboard,
   live bracket, health) that must work without a token. A global middleware
   that rejects every unauthenticated request is too broad. An opt-in FastAPI
   `Depends` guard is more precise and more idiomatic.

### Decision

**(a) Validate the ID token; reject `token_use != "id"`.**
The `CognitoJwtVerifier` validates the bearer token against the Cognito JWKS,
requires the `aud` claim to match the app client ID and `iss` to match the user
pool URL, and explicitly rejects tokens where `token_use` is not `"id"`. Any
other token type (access, refresh) raises `InvalidTokenError` → 401.

**(b) `display_name` is DB-owned, auto-generated as a randomized football handle.**
Cognito owns authentication (identity). Our Users DynamoDB table owns the user
profile. On the first authenticated request, `users.ensure_exists` creates a
record with a generated handle (e.g. `VolleyTalisman7`) using `secrets.choice`
over two football-themed word lists. The email is stored for admin purposes but
is never used to construct the name and never appears on the leaderboard. A
`ConditionalCheckFailedException` on `put_item` is silently swallowed so that
concurrent first-requests are safe.

**(c) Opt-in `Depends(require_user)` dependency over global middleware.**
Auth is enforced per-route via `require_user = Depends(...)` rather than
`app.add_middleware(...)`. This keeps public endpoints unaffected without an
explicit exclusion list. The dependency is injectable — tests swap out the
`CognitoJwtVerifier` via `app.dependency_overrides[get_verifier]` without
patching network calls.

### Consequences

**Positive**

- Public endpoints (`/health`, leaderboard, live bracket) require no
  special-casing or bypass logic.
- The fake-JWK-client seam in `CognitoJwtVerifier.__init__` lets tests validate
  the full verification path with RSA-signed tokens and no network access.
- `display_name` can be freely changed by the user in the future without
  touching Cognito at all (E2-S4 deferred edit endpoint).
- Email is stored but never exposed, satisfying basic PII hygiene on a public
  leaderboard.

**Negative / constraints**

- The `token_use == "id"` guard means the SPA must send the ID token as the
  bearer, not the access token. This is a non-default choice that must be
  documented for frontend integration (see Impacts below).
- The in-process `_seen` cache in `users.py` is per-process only. On ECS with
  multiple tasks the first request on each task will still hit DynamoDB; the
  `ConditionalCheckFailedException` guard makes this safe.

**Impacts on other work**

- **E2-S4 (frontend login):** The SPA must attach the **ID token** (not the
  access token) as the `Authorization: Bearer` header on API calls. The Cognito
  SDK response from `RespondToAuthChallenge` returns both; the frontend must
  explicitly select `AuthenticationResult.IdToken`.
- **E2-S4 (deferred):** The backend `PATCH /api/users/me` endpoint to let a
  user edit their `display_name` is deferred to E2-S4. In E2-S2, the name is
  auto-generated and read-only.
