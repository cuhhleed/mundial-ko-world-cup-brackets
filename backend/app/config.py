from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    AWS_REGION: str = "us-east-1"
    DYNAMODB_ENDPOINT_URL: str | None = None
    USERS_TABLE: str = "mundial-users"
    BRACKETS_TABLE: str = "mundial-brackets"
    MATCHES_TABLE: str = "mundial-matches"
    JWT_ISSUER: str | None = None  # E2-S2: Cognito User Pool URL

    model_config = {"env_file": ".env"}


settings = Settings()
