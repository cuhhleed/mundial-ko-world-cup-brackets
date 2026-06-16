from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.logging import configure_logging, get_logger
from app.routers import health, users

configure_logging()
logger = get_logger("mundial-ko-api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "startup",
        region=settings.AWS_REGION,
        dynamo_endpoint=settings.DYNAMODB_ENDPOINT_URL or "AWS default",
    )
    yield


app = FastAPI(title="mundial-ko-api", lifespan=lifespan)
app.include_router(health.router)
app.include_router(users.router)
