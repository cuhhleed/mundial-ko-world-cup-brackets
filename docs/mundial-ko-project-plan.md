# 2026 World Cup Bracket Maker — Project Plan

## Project Overview

A web application for the 2026 FIFA World Cup Knockout Rounds (starting June 28) that lets users predict the full 32-match bracket, compete on a global leaderboard, and follow live results. The bracket is cascading: Round of 32 winners determine predicted Round of 16 matchups, and so on through the Final.

Timeline: 14 calendar days (June 12–25), solo developer, evenings and weekends.
Estimated capacity: ~48 hours total (~2h weekday evenings, ~7h weekend days).


## Finalized Tech Stack

| Layer              | Technology                              | Notes                                              |
| ------------------ | --------------------------------------- | -------------------------------------------------- |
| Frontend           | React + TypeScript                      | SPA, deployed to S3/CloudFront                     |
| Backend API        | Python FastAPI                          | Containerized, deployed to ECS Fargate              |
| Persistent Storage | DynamoDB                                | Brackets, users, match results                     |
| Cache / Leaderboard| ElastiCache (Redis)                     | Sorted set leaderboard, live match state cache     |
| Auth               | Cognito User Pool + Google Login        | Social login only, JWT-based                       |
| Hosting            | S3 + CloudFront + Route53               | Static frontend                                    |
| Compute            | ECS Fargate + ALB                       | Backend API + data ingestion                       |
| Container Registry | ECR                                     | Docker images for Fargate tasks                    |
| Infrastructure     | Terraform                               | All AWS resources                                  |
| Data Source         | TBD                                     | Football data API, to be selected during Sprint 2  |


## Architecture Overview

Users hit the CloudFront distribution, which serves the React SPA from S3. The SPA authenticates via Cognito (Google OAuth redirect flow) and receives a JWT. All API calls go to the ALB, which routes to the FastAPI container running on ECS Fargate. The API validates the JWT, reads/writes bracket and user data to DynamoDB, and reads live match state and leaderboard rankings from ElastiCache Redis.

A separate data ingestion process (either a scheduled ECS task or a background process within the API container — to be decided during implementation) polls the external football data API on an interval, writes current match state to Redis (hash per match, with TTL), and persists completed match results to DynamoDB. When a match completes, the ingestion process triggers the scoring engine, which re-evaluates all brackets against the new result and updates the Redis sorted set leaderboard.


## Knockout Round Structure

| Round          | Matches | Matchup Predictions? | Notes                                  |
| -------------- | ------- | --------------------- | -------------------------------------- |
| Round of 32    | 16      | No                    | Matchups are pre-determined by groups  |
| Round of 16    | 8       | Yes                   | Determined by user's R32 predictions   |
| Quarterfinals  | 4       | Yes                   | Determined by user's R16 predictions   |
| Semifinals     | 2       | Yes                   | Determined by user's QF predictions    |
| Third Place    | 1       | Yes                   | Losers of user's SF predictions        |
| Final          | 1       | Yes                   | Winners of user's SF predictions       |
| **Total**      | **32**  |                       |                                        |


## Scoring System

Point values will be determined during Sprint 2 development through testing and balancing. The categories that earn points are:

| Category                | Description                                                                 | Eligible Rounds      |
| ----------------------- | --------------------------------------------------------------------------- | -------------------- |
| Correct Winner          | Predicted the correct winning team, regardless of matchup accuracy          | All rounds           |
| Correct Matchup         | Predicted the correct pairing of teams in a match                           | R16 through Final    |
| Exact Score             | Predicted the exact full-time score (90 minutes)                            | All rounds           |
| Correct PK Result       | For matches predicted as draws: predicted correct PK winner and/or score    | All rounds           |

Points per category will scale upward in later rounds (e.g., a correct Final prediction is worth more than a correct R32 prediction). Exact multipliers TBD.


---


## Epic 1: Infrastructure & DevOps

The foundational AWS infrastructure. Everything else depends on this.

### E1-S1: Terraform Project Scaffolding and Networking
**Estimate: 2.5h**

Set up the Terraform project structure (modules, environments, state backend) and provision the core networking layer.

Acceptance Criteria:
- Terraform project initialized with S3 remote state backend and DynamoDB lock table
- Module structure defined (networking, compute, storage, auth, frontend)
- VPC with public and private subnets across 2 AZs
- Internet gateway, NAT gateway, route tables configured
- Security groups defined: ALB (inbound 443/80), ECS tasks (inbound from ALB), ElastiCache (inbound from ECS), outbound internet for ECS
- `terraform plan` runs cleanly

### E1-S2: DynamoDB Tables
**Estimate: 1.5h**

Provision the DynamoDB tables with appropriate key schemas and indexes.

Acceptance Criteria:
- Users table: PK = `user_id` (Cognito sub), attributes for email, display_name, bracket_id, created_at
- Brackets table: PK = `bracket_id`, GSI on `user_id` for lookup, attributes for predictions map, total_points, created_at, status
- Matches table: PK = `match_id`, GSI on `round` for querying matches by round, attributes for teams, scores, PK results, status, kickoff_time
- On-demand billing mode (appropriate for low/unpredictable traffic)
- All provisioned via Terraform

### E1-S3: ElastiCache Redis Cluster
**Estimate: 1h**

Provision a Redis cluster in the private subnet.

Acceptance Criteria:
- Single-node Redis cluster (cache.t3.micro for cost)
- Deployed in private subnet, accessible only from ECS security group
- Subnet group and parameter group configured
- Connection endpoint output from Terraform for use by ECS task definition

### E1-S4: ECS Fargate Cluster, ALB, and ECR
**Estimate: 4h**

Provision the compute layer: container registry, ECS cluster, Fargate service, and load balancer.

Acceptance Criteria:
- ECR repository created for the API container image
- ECS cluster defined
- Fargate task definition with resource allocation (0.25 vCPU, 0.5 GB RAM), environment variables for DynamoDB table names, Redis endpoint, Cognito config
- ECS service with desired count of 1, linked to ALB target group
- ALB in public subnets with HTTPS listener (ACM certificate) and HTTP→HTTPS redirect
- Health check endpoint configured (/health)
- IAM task role with permissions for DynamoDB, ElastiCache, CloudWatch Logs
- IAM execution role with permissions for ECR pull and CloudWatch Logs

### E1-S5: S3 + CloudFront + Route53
**Estimate: 2h**

Provision the frontend hosting infrastructure.

Acceptance Criteria:
- S3 bucket configured for static website hosting (private, accessed via CloudFront OAI)
- CloudFront distribution with S3 origin, HTTPS only, custom error responses for SPA routing (404 → /index.html)
- ACM certificate for the domain (if domain is ready; otherwise use CloudFront default domain)
- Route53 A record aliased to CloudFront (if domain is ready)
- Cache behaviors configured for static assets

Dependencies: Domain name availability (can proceed without, using default CloudFront URL)

### E1-S6: Cognito User Pool + Google Identity Provider
**Estimate: 1.5h**

Provision the authentication infrastructure.

Acceptance Criteria:
- Cognito User Pool created with email as the primary attribute
- Google configured as a federated identity provider (requires OAuth client ID/secret from Google Cloud Console — manual step outside Terraform)
- App client configured with OAuth 2.0 flows (authorization code grant), callback/logout URLs pointing to the frontend domain
- Hosted UI domain configured (or custom domain if available)
- User pool outputs (pool ID, client ID, domain) available for backend and frontend configuration

Dependencies: Google Cloud Console OAuth app must be created manually before applying Terraform. Document this as a prerequisite.

### E1-S7: Deployment Scripts
**Estimate: 1h**

Simple shell scripts for building and deploying both frontend and backend.

Acceptance Criteria:
- `deploy-api.sh`: builds Docker image, pushes to ECR, forces new ECS deployment
- `deploy-frontend.sh`: builds React app, syncs to S3, invalidates CloudFront cache
- Both scripts parameterized for environment

**Epic 1 Total Estimate: ~13.5h**


---


## Epic 2: Authentication

End-to-end Google login flow, from the React UI through Cognito to JWT-validated API calls.

### E2-S1: FastAPI Project Scaffold + Containerization
**Estimate: 2.5h**

Bootstrap the FastAPI project and get it deploying to ECS.

Acceptance Criteria:
- FastAPI project with standard structure (routers, models, services, middleware)
- /health endpoint returning 200
- Dockerfile (Python 3.12 slim base, pip install, uvicorn entrypoint)
- Docker image builds and runs locally
- Image pushed to ECR and Fargate task starts successfully
- ALB health check passes
- Environment variables loaded for DynamoDB, Redis, Cognito config

### E2-S2: Cognito JWT Validation Middleware
**Estimate: 2h**

FastAPI middleware that validates the Cognito JWT on protected endpoints.

Acceptance Criteria:
- Middleware fetches Cognito JWKS (cached in-memory) and validates the Authorization header bearer token
- Extracts user_id (sub), email, and display_name from token claims
- Injects authenticated user context into request state
- Returns 401 for missing/invalid/expired tokens
- /health and other public endpoints bypass auth
- First authenticated request auto-creates a user record in DynamoDB if one doesn't exist

### E2-S3: React Project Scaffold + Deployment
**Estimate: 2h**

Bootstrap the React app and get it deploying to S3/CloudFront.

Acceptance Criteria:
- React + TypeScript project (Vite)
- Basic routing (react-router): home, bracket, leaderboard, live bracket
- API client module configured with the ALB base URL
- Builds to static assets
- Deployed to S3 and accessible via CloudFront URL
- SPA routing works (CloudFront 404 → index.html)

### E2-S4: Frontend Google Login Flow
**Estimate: 2h**

Implement the Cognito-hosted UI redirect flow for Google Sign-In.

Acceptance Criteria:
- Login button redirects to the Cognito hosted UI (Google sign-in)
- Cognito redirects back to the app with an authorization code
- Frontend exchanges the code for tokens (ID token, access token, refresh token) via the Cognito token endpoint
- Tokens stored in memory (not localStorage due to artifact constraints — use React context/state)
- Access token attached to all API requests as a Bearer token
- Logged-in state persists across the session, user sees their display name / email
- Logout button clears tokens and redirects to Cognito logout endpoint
- Unauthenticated users can view the live bracket and leaderboard but cannot create a bracket

> **Note (pivot):** E1-S6 replaced Google OAuth / Cognito hosted UI with **passwordless email OTP** (Cognito `USER_AUTH` + `EMAIL_OTP`, no hosted UI, no client secret). The acceptance criteria above still describe the old hosted-UI redirect flow and need rewriting to the OTP flow: the SPA calls `InitiateAuth` (AuthFlow `USER_AUTH`) → `RespondToAuthChallenge` directly against the Cognito public API, no authorization-code exchange or hosted-UI redirect.
>
> **Cognito config injection (build-time, Option A):** The SPA needs `region`, `user_pool_id`, and `app_client_id` to initialize the Cognito SDK. These are non-secret and are exposed as root Terraform outputs (`aws_region`, `cognito_user_pool_id`, `cognito_app_client_id`) on both the dev and prod environments. The frontend build/deploy step must:
> - Run `terraform output -raw <name>` (or read all outputs as JSON) after `apply` to fetch the three values.
> - Export them as Vite build-time env vars (e.g. `VITE_AWS_REGION`, `VITE_COGNITO_USER_POOL_ID`, `VITE_COGNITO_APP_CLIENT_ID`) before `vite build` so they are inlined into the bundle, then sync to S3.
> - Because the values are inlined at build time, rotating the app client requires a frontend rebuild + redeploy (acceptable — these IDs are effectively static after first creation).

**Epic 2 Total Estimate: ~8.5h**


---


## Epic 3: Bracket Maker

The core feature. Users create a cascading bracket prediction and view it with results overlaid.

### E3-S1: Bracket Data Model and DynamoDB Schema
**Estimate: 1.5h**

Design and implement the bracket data model, including the cascading matchup derivation logic.

Acceptance Criteria:
- Bracket prediction structure defined: for each of the 32 matches, store predicted_winner, predicted_home_score, predicted_away_score, and optionally predicted_pk_winner, predicted_pk_home_score, predicted_pk_away_score (for predicted draws)
- Utility functions to derive downstream matchups from upstream predictions (e.g., given R32 predictions, compute the implied R16 matchups)
- Bracket stored as a single DynamoDB item (predictions as a nested map) to enable atomic reads/writes
- Match slot identifiers defined (e.g., R32-1 through R32-16, R16-1 through R16-8, etc.) with a clear mapping of which upstream matches feed into which downstream slots

### E3-S2: Create Bracket API
**Estimate: 2h**

Endpoint for submitting a new bracket.

Acceptance Criteria:
- POST /api/brackets accepts the full bracket prediction payload
- Validates that predictions are structurally complete (all 32 matches have predictions) and internally consistent (cascading matchups are logically coherent — if you pick Team A in R32, Team A must appear in your R16 matchup)
- Enforces one bracket per user (checks DynamoDB for existing bracket_id on the user record, rejects if one exists)
- Stores the bracket in DynamoDB, updates the user record with the bracket_id
- Returns the created bracket with its ID

### E3-S3: Late Bracket Logic
**Estimate: 2h**

Handle brackets created after some matches have already been played.

Acceptance Criteria:
- GET /api/brackets/template returns the current bracket template: for completed matches, the results are pre-filled and locked (user cannot override); for in-progress matches, results are pre-filled and locked; for upcoming matches, slots are open for prediction
- The cascading logic respects locked results: if R32-1 is complete, the R16 matchup that R32-1 feeds into uses the actual winner, not a user prediction
- Late brackets earn zero points for any locked matches (no retroactive credit)
- Frontend uses this template to render the bracket creation UI with locked/open indicators

### E3-S4: Get Bracket API
**Estimate: 1.5h**

Endpoint for retrieving a user's bracket with current results overlaid.

Acceptance Criteria:
- GET /api/brackets/{bracket_id} returns the bracket predictions alongside actual results for completed matches
- Response includes per-match scoring breakdown (points earned per category, which predictions were correct)
- Response includes total points
- GET /api/brackets/me (authenticated) returns the current user's bracket

### E3-S5: Bracket Creation UI — Cascading Selection
**Estimate: 5h**

The primary user-facing interface for building a bracket prediction.

Acceptance Criteria:
- Displays the full bracket structure: R32 through Final, visually resembling a tournament bracket
- R32 matchups are pre-populated with the actual team pairings
- User selects a winner for each R32 match; selected winners automatically populate as the matchup for the corresponding R16 slot
- User selects R16 winners, which populate QF matchups, and so on through the Final
- Changing an upstream pick cascades: if the user changes an R32 winner, the downstream R16 matchup updates, and any predictions in that R16 slot (and further downstream) are cleared, forcing the user to re-predict
- UI clearly distinguishes between rounds that are ready to predict and rounds that are waiting on upstream selections
- Responsive layout that works on both desktop and mobile

### E3-S6: Bracket Creation UI — Score and PK Predictions
**Estimate: 3h**

Score input layer on top of the bracket selection UI.

Acceptance Criteria:
- For each match, after selecting a winner, user enters predicted home and away scores
- If the entered scores are a draw, a PK prediction section appears: user predicts PK winner and PK scoreline
- Score inputs are validated (non-negative integers, winner's score must be ≥ loser's score unless it's a draw with PK prediction)
- Submit button is enabled only when all 32 matches have complete predictions (winner + scores, plus PK where applicable)
- On submit, calls POST /api/brackets, shows confirmation, and transitions to the bracket viewer

### E3-S7: Bracket Viewer
**Estimate: 3h**

Post-creation read-only view of the user's bracket with live results overlaid.

Acceptance Criteria:
- Displays the user's bracket predictions in the same visual format as the creation UI
- For completed matches, overlays the actual result next to the prediction
- Visual indicators for each prediction category: correct winner (green check), incorrect winner (red X), correct matchup (highlighted), exact score (gold star or similar), correct PK result (distinct indicator)
- Total points displayed prominently, with a breakdown available (points by round, points by category)
- For matches not yet played, shows the user's prediction without result overlay
- Link/button to view the global leaderboard

**Epic 3 Total Estimate: ~18h**


---


## Epic 4: Scoring & Leaderboard

The point system and competitive ranking.

### E4-S1: Scoring Engine
**Estimate: 3h**

Backend service that evaluates bracket predictions against actual results.

Acceptance Criteria:
- Scoring function takes a bracket and a set of completed match results, returns a per-match point breakdown and total score
- Evaluates all four scoring categories: correct winner, correct matchup, exact score, correct PK result
- Point values per category per round are defined in a configuration file (not hardcoded) for easy tuning
- Handles partial brackets (late entries with locked matches score 0 for those matches)
- Handles cascading matchup evaluation: a matchup prediction is correct if both teams in the user's predicted pairing match the actual pairing, regardless of whether the user predicted the correct upstream path to get there
- Unit tests covering key scoring scenarios:
  - Correct winner, wrong score
  - Correct exact score
  - Correct matchup + correct winner
  - Wrong matchup, but correct winner (user predicted Team A wins, Team A did win, but against a different opponent than predicted)
  - Draw with correct PK prediction
  - Late bracket with locked matches

### E4-S2: Scoring Trigger and Leaderboard Updates
**Estimate: 2h**

When a match completes, re-score all affected brackets and update the Redis leaderboard.

Acceptance Criteria:
- When the data ingestion process writes a match result with status "completed" to DynamoDB, it triggers the scoring engine
- Scoring engine scans all brackets from DynamoDB (at low user counts, a full scan is acceptable; note: if user count grows, this should be refactored to a fan-out pattern)
- For each bracket, recalculates total points and updates the bracket's total_points in DynamoDB
- Updates the Redis sorted set leaderboard: ZADD leaderboard {total_points} {user_id}
- Logs scoring results for debugging

### E4-S3: Leaderboard API
**Estimate: 1.5h**

Endpoints for reading the leaderboard.

Acceptance Criteria:
- GET /api/leaderboard returns the top N users (default 50) with rank, display_name, and total points, read from the Redis sorted set (ZREVRANGE with WITHSCORES)
- GET /api/leaderboard/me (authenticated) returns the current user's rank (ZREVRANK) and total points (ZSCORE)
- Response includes total participant count (ZCARD)

### E4-S4: Leaderboard Frontend
**Estimate: 2h**

Leaderboard page in the React app.

Acceptance Criteria:
- Displays the ranked list of users with position, display name, and total points
- Current user's row is highlighted if they are logged in
- If the user is not in the visible top N, their rank and points are shown separately (e.g., "You are ranked #47 with 23 points")
- Auto-refreshes on a reasonable interval (every 60 seconds, or manual refresh button)
- Accessible to unauthenticated users (view-only)

**Epic 4 Total Estimate: ~8.5h**


---


## Epic 5: Live Bracket & Data Ingestion

Live match results and the football data pipeline.

### E5-S1: Data Source Selection and Integration
**Estimate: 2h**

Research, select, and integrate a football data API. **Data source is TBD at planning time.** Candidates include API-Football (via RapidAPI), football-data.org, and SportRadar.

Acceptance Criteria:
- Data source selected based on: KO round coverage for 2026 World Cup, real-time or near-real-time score updates, reasonable free/low-cost tier, reliable API documentation
- API client module implemented in the backend with functions to fetch current match state, completed results, and upcoming match schedules
- Error handling and retry logic for API failures
- API credentials stored as environment variables (injected via ECS task definition)

Dependencies: This is a blocking dependency for E5-S2 through E5-S4 and E4-S2. Must be completed before live data features can be tested with real data.

### E5-S2: Data Ingestion Service
**Estimate: 3h**

Background process that polls the data source and writes to Redis and DynamoDB.

Acceptance Criteria:
- Polling loop runs on a configurable interval (e.g., every 60 seconds during live matches, every 5 minutes otherwise)
- Writes current match state to Redis as a hash per match: `match:{match_id}` with fields for status, home_team, away_team, home_score, away_score, minute, etc., with a TTL
- When a match transitions to "completed," writes the final result to DynamoDB (Matches table) and triggers the scoring engine (E4-S2)
- Populates initial match schedule (R32 matchups with teams, kickoff times) into DynamoDB from the data source
- Implementation decision to be made: run as a separate ECS task (cleaner separation, independent scaling) or as a background thread within the API container (simpler deployment, shared resources). For a solo project, a background thread with an async loop inside the FastAPI process is likely the pragmatic choice.

### E5-S3: Live Results API
**Estimate: 1h**

Endpoints for the frontend to fetch live bracket data.

Acceptance Criteria:
- GET /api/matches returns all matches grouped by round, with current state (teams, scores, status, kickoff time), read from Redis for live/recent matches, DynamoDB for historical
- GET /api/matches/{match_id} returns detailed state for a single match
- Response format is consistent whether the match is upcoming, live, or completed

### E5-S4: Live Bracket Frontend
**Estimate: 3h**

Real-time bracket display showing actual tournament results.

Acceptance Criteria:
- Displays the full bracket structure with actual results filled in as matches complete
- Live matches show current score with a visual "live" indicator
- Upcoming matches show team names (or "TBD" for matches whose participants depend on earlier results) and kickoff times
- Completed matches show final score, including PK result if applicable
- Auto-refreshes live match data on a reasonable interval (every 30-60 seconds)
- Accessible to unauthenticated users
- Visually consistent with the bracket creation and bracket viewer UIs (shared bracket component with different rendering modes)

**Epic 5 Total Estimate: ~9h**


---


## Sprint Plan

### Sprint 1: Foundation + Bracket Core (June 12–18)

**Sprint Goal:** AWS infrastructure fully provisioned, authentication working end-to-end, bracket creation API functional, frontend scaffold deployed.

**Capacity:** ~24 hours (5 weekday evenings × ~2h + 2 weekend days × ~7h)

| Day | Date       | Type    | Hours | Stories                                           |
| --- | ---------- | ------- | ----- | ------------------------------------------------- |
| 1   | Thu Jun 12 | Evening | 2h    | E1-S1: Terraform scaffolding + VPC/networking      |
| 2   | Fri Jun 13 | Evening | 2h    | E1-S2: DynamoDB tables, E1-S3: ElastiCache cluster |
| 3   | Sat Jun 14 | Full    | 7h    | E1-S4: ECS Fargate + ALB (4h), E1-S5: S3 + CloudFront (2h), E1-S6: Cognito (1h) |
| 4   | Sun Jun 15 | Full    | 7h    | E2-S1: FastAPI scaffold + deploy (2.5h), E2-S2: JWT middleware (2h), E2-S3: React scaffold + deploy (2h), start E2-S4 |
| 5   | Mon Jun 16 | Evening | 2h    | E2-S4: Frontend Google login flow                  |
| 6   | Tue Jun 17 | Evening | 2h    | E3-S1: Bracket data model + DynamoDB schema         |
| 7   | Wed Jun 18 | Evening | 2h    | E3-S2: Create bracket API                           |

**Sprint 1 Definition of Done:**
- `terraform apply` provisions all infrastructure successfully
- FastAPI container running on Fargate, health check passing through ALB
- React app served via CloudFront, SPA routing working
- Google login works: click button → Cognito redirect → Google → back to app with valid JWT
- Authenticated API calls succeed (JWT validated, user record created in DynamoDB)
- POST /api/brackets creates and stores a bracket in DynamoDB
- One-bracket-per-user enforced

**Risks:**
- ECS Fargate networking is the most likely time sink (security group misconfigurations, ALB target group health checks failing, task role permission issues). Budget extra debugging time on Day 3.
- Cognito Google IdP setup requires a manual step in the Google Cloud Console (OAuth consent screen, credentials). Do this before Day 3.
- If infrastructure takes longer than expected, E3-S1 and E3-S2 can shift to early Sprint 2 without blocking other work.


### Sprint 2: Features + Live Data + Polish (June 19–25)

**Sprint Goal:** Bracket creation and viewing fully functional, live data flowing, leaderboard operational, app ready for public sharing.

**Capacity:** ~24 hours (5 weekday evenings × ~2h + 2 weekend days × ~7h)

| Day | Date       | Type    | Hours | Stories                                           |
| --- | ---------- | ------- | ----- | ------------------------------------------------- |
| 8   | Thu Jun 19 | Evening | 2h    | E3-S3: Late bracket logic + GET bracket API (E3-S4) |
| 9   | Fri Jun 20 | Evening | 2h    | E3-S5: Bracket creation UI — start cascading selection |
| 10  | Sat Jun 21 | Full    | 7h    | E3-S5: Bracket creation UI continued (3h), E3-S6: Score/PK inputs (3h), E5-S1: Data source research (1h) |
| 11  | Sun Jun 22 | Full    | 7h    | E5-S2: Data ingestion service (3h), E4-S1: Scoring engine (3h), E1-S7: Deployment scripts (1h) |
| 12  | Mon Jun 23 | Evening | 2h    | E4-S2: Scoring trigger + leaderboard updates, E4-S3: Leaderboard API |
| 13  | Tue Jun 24 | Evening | 2h    | E3-S7: Bracket viewer (start), E5-S3: Live results API |
| 14  | Wed Jun 25 | Evening | 2h    | E3-S7: Bracket viewer (finish), E5-S4: Live bracket frontend (start) |

**Remaining after Sprint 2 (June 26–27, buffer days before KO starts June 28):**
- E5-S4: Live bracket frontend polish
- E4-S4: Leaderboard frontend
- End-to-end testing with mock data
- Bug fixes
- Point system balancing with test brackets

**Sprint 2 Definition of Done:**
- User can create a full cascading bracket with score predictions through the UI
- Late brackets correctly auto-fill completed match results
- Bracket viewer shows predictions vs. actuals with visual indicators
- Data ingestion service polls the football API and writes to Redis/DynamoDB
- Completed matches trigger the scoring engine, which updates bracket scores and the Redis leaderboard
- Leaderboard page displays rankings
- Live bracket page shows current tournament state

**Risks:**
- The bracket creation UI (E3-S5 + E3-S6) is the most complex frontend work — cascading state management across 6 rounds with validation. If it runs long, deprioritize visual polish and ship a functional but plain UI.
- Data source selection (E5-S1) is a blocker for all live features. If no suitable free API is found, mock the data ingestion interface and plug in the real source later. The ingestion service should be designed behind an adapter/interface regardless.
- Scoring engine correctness is critical. The unit tests in E4-S1 are not optional — edge cases in cascading matchup scoring are where bugs will hide.
- The schedule is intentionally tight on the leaderboard frontend (E4-S4) and live bracket frontend (E5-S4). These are the simplest UIs (a ranked list and a read-only bracket display), so they can tolerate being built quickly or carried into buffer days.


---


## Key Risks and Mitigations

| Risk | Impact | Mitigation |
| ---- | ------ | ---------- |
| ECS Fargate setup takes longer than estimated | Delays all backend work | Start infra on Day 1, leave Day 3 (weekend) as the overflow day for debugging |
| No suitable free football data API | Live features and scoring cannot be tested with real data | Design ingestion service behind an adapter interface; build a mock data provider for development and testing |
| Bracket creation UI complexity exceeds estimate | Core feature is incomplete | Build a functional-first version (no visual polish) and iterate; share a bracket component between creation, viewing, and live display |
| Scoring edge cases in cascading matchup logic | Incorrect point calculations undermine the leaderboard | Comprehensive unit tests are mandatory in E4-S1; test with adversarial bracket scenarios |
| Solo developer burnout over 14 days of evening/weekend work | Reduced velocity in Sprint 2 | Protect one evening mid-sprint as a break; cut scope on visual polish before cutting features |
| Cognito/Google OAuth misconfiguration | Auth doesn't work, blocking bracket creation | Set up the Google Cloud OAuth app before starting Terraform; test the hosted UI flow manually before integrating with React |


## Data Model Reference

### DynamoDB Tables

**Users**
- Partition Key: `user_id` (String, Cognito sub)
- Attributes: `email`, `display_name`, `bracket_id` (nullable), `created_at`

**Brackets**
- Partition Key: `bracket_id` (String, UUID)
- GSI: `user_id-index` on `user_id` for lookup by user
- Attributes: `user_id`, `predictions` (Map — nested structure of all 32 match predictions), `total_points` (Number), `created_at`, `status`

**Matches**
- Partition Key: `match_id` (String)
- GSI: `round-index` on `round` for querying by round
- Attributes: `round`, `match_number`, `home_team`, `away_team`, `home_score`, `away_score`, `pk_home_score`, `pk_away_score`, `pk_winner`, `status` (scheduled/live/completed), `kickoff_time`

### Redis Key Schema

| Key Pattern              | Type       | Purpose                                    | TTL     |
| ------------------------ | ---------- | ------------------------------------------ | ------- |
| `leaderboard`            | Sorted Set | Global ranking (member=user_id, score=pts) | None    |
| `match:{match_id}`       | Hash       | Live match state (status, scores, minute)  | 24h     |
| `round:{round}:matches`  | List       | Match IDs belonging to a round             | None    |


## Decisions to Make During Development

1. **Data source**: Which football data API to use. Evaluate during E5-S1 (Day 10).
2. **Point values**: Specific point allocations per scoring category per round. Define during E4-S1 (Day 11), iterate based on testing.
3. **Data ingestion deployment model**: Separate ECS task vs. background thread in the API container. Decide during E5-S2 (Day 11).
4. **Domain name**: Whether a custom domain is ready for Route53 + CloudFront + ALB. If not, use default AWS-provided URLs.
5. **Bracket UI layout**: Horizontal scrolling bracket vs. vertical round-by-round accordion for mobile. Decide during E3-S5 (Days 9-10).
