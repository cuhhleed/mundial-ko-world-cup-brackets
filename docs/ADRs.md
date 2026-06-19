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

---

## ADR-003: Auth flow pivot — SES email delivery, split sign-up/login, bracket-gated registration

- **Status:** Accepted
- **Date:** 2026-06-16
- **Sprint:** E2-S4 (Frontend auth + bracket submission)
- **Supersedes:** Parts of ADR-001 (email delivery, auth flow assumptions)

### Context

Three problems with the auth implementation from ADR-001 became apparent during
E2-S4 development:

1. **Cognito default email is unreliable.** `COGNITO_DEFAULT` sends from
   `no-reply@verificationemail.com`, which is spam-filtered or silently dropped
   by many providers. OTPs never arrived during testing. The 50 email/day cap
   also makes development painful, and public launch impossible without a
   change.

2. **The auth flow assumed login-then-use, but the product needs use-then-sign-up.**
   The bracket page was behind a `RequireAuth` gate. The actual UX goal is for
   anyone to build a bracket without an account, and only require auth at
   submission time — sign-up should be inseparable from bracket submission.

3. **Sign-up and login were conflated.** Cognito's `USER_AUTH` + `EMAIL_OTP`
   flow auto-creates users on `InitiateAuth` with an unknown email, making it
   impossible to distinguish new vs. returning users. This matters because
   sign-up must be coupled to bracket submission (no empty accounts), while
   login is for returning users viewing their existing bracket.

### Decision

**(a) Replace Cognito default email with SES.**

- Terraform: change `email_sending_account` from `"COGNITO_DEFAULT"` to
  `"DEVELOPER"` and set `source_arn` to a verified SES domain identity.
- Request SES production access immediately — sandbox mode restricts sending to
  individually verified addresses only, blocking public sign-ups. AWS approval
  typically takes 24–48 hours; with KO rounds starting June 28, this is
  time-critical.
- No frontend or backend code changes required — the OTP flow is identical;
  only the delivery path changes under the hood.

**(b) Bracket page is public; sign-up happens via modal overlay at submission.**

- The bracket builder is fully accessible without authentication. Users build
  their R32-through-Final predictions as anonymous visitors.
- "Submit Bracket" triggers a sign-up modal overlay on the bracket page. The
  bracket component stays mounted, preserving React state through the OTP
  flow — no serialization to sessionStorage, no route transitions.
- After OTP verification, the frontend immediately POSTs the bracket payload.
  The backend's `require_user` dependency fires `ensure_exists` (creating the
  user record), then the bracket is saved and linked to the user. The user
  lands as authenticated with their bracket already locked in.
- A clear warning about bracket finality is shown before entering the sign-up
  flow (pre-submit confirmation), not after.

**(c) Sign-up and login are separated with an email existence check.**

- A new unauthenticated backend endpoint (`GET /api/users/exists?email=...`)
  returns a boolean indicating whether a user record exists for the given
  email.
- **Sign-up modal** (bracket page): calls the existence endpoint first. If the
  email is already registered, rejects with "You already have an account —
  log in instead." Otherwise proceeds with `InitiateAuth` → OTP → bracket
  submission.
- **Login page** (`/login`): calls the existence endpoint first. If the email
  is not registered, rejects with "No account found — build a bracket to sign
  up." Otherwise proceeds with `InitiateAuth` → OTP → redirect to bracket
  page.
- This enforces the invariant that every account has a bracket: sign-up is
  the only account creation path, and it is inseparable from bracket
  submission.

**(d) Post-submission bracket is read-only; no edits allowed.**

- Once submitted, the bracket page for an authenticated user displays their
  locked predictions in read-only mode. No edit capability.
- This keeps logic clean given that late submissions are allowed (editing
  would require re-scoring and cascading-clear logic that adds complexity
  disproportionate to the value).

**(e) Login is a separate page; post-login redirects to the bracket page.**

- Login lives at `/login` as a standalone page — returning users navigate
  there directly. After successful OTP verification, they are redirected to
  the bracket page (showing their locked predictions).
- The navbar shows a "Login" link when unauthenticated. After login, it shows
  the user's display name and a logout action.

### Consequences

**Positive**

- SES gives reliable email delivery, deliverability metrics, and no daily cap
  (in production mode).
- The bracket-first flow reduces friction: users invest in their predictions
  before being asked to create an account, increasing conversion.
- The sign-up/login split with an existence check cleanly enforces the
  "no empty accounts" invariant without fighting Cognito's auto-creation
  behavior.
- Read-only post-submission eliminates an entire class of edit/re-score
  complexity.

**Negative / constraints**

- The existence-check endpoint reveals whether an email is registered. This
  is an acceptable trade-off for a bracket prediction app (not
  security-sensitive), and `prevent_user_existence_errors` on the Cognito
  client still guards the auth layer itself.
- SES production access approval is a blocking external dependency for public
  launch. Sandbox mode is sufficient for development with manually verified
  test addresses.
- No bracket editing means a user who makes a mistake must live with it.
  The pre-submit warning mitigates this.

**Impacts on other work**

- **Terraform (auth module):** `email_configuration` block changes to
  `DEVELOPER` + SES `source_arn`. New SES resource (domain identity +
  verification) needed.
- **Backend:** New `GET /api/users/exists?email=...` endpoint (public, no
  auth). Bracket creation endpoint must enforce one-bracket-per-user.
- **Frontend (auth):** `RequireAuth` removed from the bracket route.
  `AuthContext` refactored: sign-up modal component (on bracket page) and
  login page component replace the current unified `Login.tsx`. `cognito.ts`
  stays mostly unchanged (same `InitiateAuth`/`RespondToAuthChallenge` calls).
- **Frontend (bracket page):** Must manage two states — editable (anonymous
  or authenticated-without-bracket, though the latter shouldn't exist) and
  read-only (authenticated with submitted bracket). Submit button triggers
  sign-up modal.
- **ADR-001:** The email delivery section ("Cognito's default sender for
  now") is superseded by this ADR. The OTP auth mechanism itself remains
  valid.

---

## ADR-004: Auth pivot to Google Sign-In (ID token)

- **Status:** Accepted
- **Date:** 2026-06-19
- **Sprint:** E2-S4 (Frontend auth + bracket submission)
- **Supersedes:** ADR-001 (auth mechanism), ADR-003 (SES delivery, OTP flow,
  sign-up/login split). Retargets ADR-002 (JWT validation) from Cognito to
  Google.

### Context

ADR-003 pivoted email delivery to SES to make the Cognito `EMAIL_OTP` flow
reliable. That pivot is now blocked: SES is stuck in sandbox, the production-
access request has had no traction in 7 days, and on a basic support plan there
is no path to prioritize it. Sandbox mode can only send to individually verified
addresses, so public sign-up is impossible. With KO rounds starting June 28 and
most application logic still unbuilt, we cannot spend more time operating an
email channel.

Reframing the requirement: auth exists to **gate bracket creation** (prevent
submission spam / sybil) and **keep leaderboard integrity** with a **stable,
recoverable identity**. Email was a *means* to those ends, not a requirement.
Any identity that is moderately hard to mass-produce and lets a user return to
their bracket satisfies the goal.

We evaluated whether Google Sign-In reintroduces an SES-style approval
dependency. It does not, for our scope set:

- Google's **mandatory** OAuth verification (demo video, review by Google's
  OAuth team, can be denied) is triggered only by **sensitive/restricted**
  scopes. Apps using **only non-sensitive scopes** (`openid`, `email`,
  `profile`) are not subject to it.
- **Brand verification** (showing app name + logo on the consent screen) is an
  *optional, lighter-weight* step and is **non-blocking** for sign-in.

This was confirmed empirically with a throwaway spike (`spikes/google-oauth/`)
using Google Identity Services' "Sign in with Google" (ID-token /
authentication) button. Two unaffiliated accounts — neither project owner nor
listed test user — signed in cleanly in **Testing** publishing status: no
consent warning, no "unverified app" screen. The returned ID token carried
`iss = https://accounts.google.com`, `aud = <client_id>`, a stable `sub`,
`email`, and `email_verified` — exactly the claims the backend needs. The
authentication-only flow (no API scopes) sits outside the verification/consent
machinery entirely.

### Decision

**(a) Google Sign-In (ID token) becomes the sole identity provider.**

- **Frontend:** Google Identity Services "Sign in with Google" button yields a
  Google-issued ID token (JWT).
- **Backend:** validate the ID token against Google's JWKS
  (`https://www.googleapis.com/oauth2/v3/certs`), requiring
  `iss ∈ {https://accounts.google.com, accounts.google.com}` and
  `aud == GOOGLE_CLIENT_ID`. `user_id = sub`. This reuses the pluggable
  verifier seam from ADR-002 (the Cognito verifier is replaced/generalized to a
  Google verifier); the Cognito-specific `token_use == "id"` guard is dropped
  (Google ID tokens carry no `token_use`).
- **Scopes** are limited to `openid`, `email`, `profile` (non-sensitive),
  deliberately avoiding the verification review.
- The OAuth app will be **published to Production** before launch (self-serve,
  no blocking review for our scopes). We proceed with caution and verify
  externally-facing sign-in behavior before relying on it.
- Backend config gains `GOOGLE_CLIENT_ID` (the `aud`) plus the fixed Google
  issuer/JWKS; the frontend gains `VITE_GOOGLE_CLIENT_ID`. The Google OAuth
  client is created/managed in the Google Cloud Console (no first-class
  Terraform resource in this AWS-centric setup); its client ID is documented and
  injected as a build/env var.

**(b) Stateless session model: short-lived ID token + silent re-auth.**

The GIS button returns only a ~1-hour ID token and **no refresh token** (unlike
Cognito's 30-day refresh). The frontend sends the ID token as
`Authorization: Bearer` and the backend validates it per request, as today. On
expiry, the frontend silently re-triggers Google sign-in (a frictionless
one-tap while the Google session is active). No backend-minted session is
introduced. "Return to your bracket" is satisfied because identity is the
server-side Google `sub`; cross-device works for free (it was not a hard
requirement).

**(c) The OTP sign-up/login split and `/exists` endpoint are removed.**

The ADR-003 split (separate sign-up modal vs. login page, plus
`GET /api/users/exists`) existed solely because Cognito's `USER_AUTH` flow
auto-created users and could not distinguish new from returning. Google handles
new-vs-returning transparently, so that complexity is deleted. Preserved from
ADR-003: the bracket-first UX (build anonymously → "Submit Bracket" → Google
sign-in → POST bracket), `ensure_exists` user bootstrapping (now keyed on Google
`sub`), the one-bracket-per-user invariant, and read-only post-submission. The
`/login` page remains for returning users — now just a Google button.

Retiring the now-unused Cognito + SES infrastructure is **out of scope for this
ADR** and tracked as **TASK-001** (`docs/pendings_tasks.md`), gated on Google
auth being set up and validated in the live app.

### Consequences

**Positive**

- Removes the operated email channel *and* the AWS approval dependency that was
  blocking launch — the critical-path blocker is gone, with no new
  approval-gated dependency in its place.
- Stronger sybil resistance than throwaway email; stable, recoverable identity
  (Google `sub`); cross-device for free.
- Net code reduction: deletes the OTP flow, `/exists` endpoint, and the
  sign-up/login split — while reusing the JWT verifier seam. (Removing the
  Cognito + SES Terraform is deferred to TASK-001.)
- One-click sign-in is lower-friction than email + code.

**Negative / constraints**

- Google-only excludes users without a Google account (accepted for a side
  project; coverage is high).
- Runtime dependency on Google's auth availability (negligible).
- No refresh token: sessions are bounded by the ~1-hour ID token and rely on
  silent re-auth; if no Google session is present the user re-clicks sign-in
  (acceptable — one tap).
- Brand verification (polished consent screen with name + logo) is still
  pending; non-blocking, deferred.
- The OAuth client lives outside Terraform (Google Cloud Console) — a config-
  drift surface; mitigated by documenting it and injecting the client ID via
  env var.
- Cognito + SES remain provisioned until TASK-001 runs; until then the old
  infrastructure coexists unused.

**Impacts on other work**

- **ADR-001:** the `EMAIL_OTP` mechanism is fully superseded.
- **ADR-002:** the validation *strategy* (validate an ID token, derive identity,
  `ensure_exists`, opt-in `require_user`) remains valid; only issuer/JWKS/`aud`
  retarget Cognito → Google, and the `token_use` guard is dropped.
  `display_name` DB-ownership is unchanged.
- **ADR-003:** SES delivery, the OTP flow, the sign-up/login split, and
  `/exists` are superseded; the bracket-first submit UX, one-bracket invariant,
  and read-only post-submission are retained.
- **Backend:** introduce the Google verifier and config swap; remove the
  `/exists` route. Evaluate whether `users.exists_by_email` and the Users
  `email-index` GSI are still used anywhere before removing them.
- **Frontend:** replace `cognito.ts` with a GIS module; drop the existence-check
  from `SignUpModal`; `AuthContext` stores the Google ID token; `tokens.ts`
  simplifies.
- **TASK-001:** decommission Cognito + SES (Terraform `auth` module, the
  `cognito_*` outputs, and the `VITE_COGNITO_*` build vars), gated on the Google
  auth path being live and validated.
- **Spike:** `spikes/google-oauth/` is to be deleted once this ADR is recorded.
