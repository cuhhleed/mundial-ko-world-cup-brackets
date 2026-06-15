from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.logging import configure_logging, get_logger
from app.middleware.auth import AuthMiddleware
from app.routers import health

configure_logging()
logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "startup",
        region=settings.AWS_REGION,
        dynamo_endpoint=settings.DYNAMODB_ENDPOINT_URL or "AWS default",
    )
    yield


app = FastAPI(title="mundial-ko-api", lifespan=lifespan)
app.add_middleware(AuthMiddleware)
app.include_router(health.router)
