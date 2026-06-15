from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ENVIRONMENT: str = "local"
    AWS_REGION: str = "us-east-1"
    DYNAMODB_ENDPOINT_URL: str | None = None
    USERS_TABLE: str = "mundial-users"
    BRACKETS_TABLE: str = "mundial-brackets"
    MATCHES_TABLE: str = "mundial-matches"
    REDIS_ENDPOINT: str = "localhost"
    REDIS_PORT: int = 6379
    JWT_ISSUER: str | None = None  # E2-S2: Cognito User Pool URL
    COGNITO_USER_POOL_ID: str | None = None  # E2-S2: Cognito User Pool ID
    COGNITO_APP_CLIENT_ID: str | None = None  # E2-S2: token audience (aud) validation

    model_config = {"env_file": ".env"}


settings = Settings()
