from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ENVIRONMENT: str = "local"
    AWS_REGION: str = "us-east-1"
    DYNAMODB_ENDPOINT_URL: str | None = None
    USERS_TABLE: str = "mundial-ko-local-users"
    BRACKETS_TABLE: str = "mundial-ko-local-brackets"
    MATCHES_TABLE: str = "mundial-ko-local-matches"
    REDIS_ENDPOINT: str = "localhost"
    REDIS_PORT: int = 6379
    JWT_ISSUER: str | None = None  # E2-S2: Cognito User Pool URL (TASK-001: remove)
    COGNITO_USER_POOL_ID: str | None = None  # E2-S2: Cognito User Pool ID (TASK-001: remove)
    COGNITO_APP_CLIENT_ID: str | None = None  # E2-S2: token audience (TASK-001: remove)
    GOOGLE_CLIENT_ID: str | None = None  # E2-S4: Google OAuth client ID (token audience)
    FRONTEND_URL: str = "http://localhost:5173"
    AWS_ACCESS_KEY_ID: str = "DUMMYIDEXAMPLE"
    AWS_SECRET_ACCESS_KEY: str = "DUMMYSECRETANDKEYEXAMPLE"
    ESPN_BASE_URL: str = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world"
    INGESTION_POLL_INTERVAL: int = 60
    INGESTION_PRE_KICKOFF_BUFFER: int = 300
    INGESTION_HEARTBEAT_INTERVAL: int = 3600
    CLOUDWATCH_NAMESPACE: str = "MundialKO"

    model_config = {"env_file": ".env"}


settings = Settings()
