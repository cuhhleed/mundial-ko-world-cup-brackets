import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.middleware.auth import AuthMiddleware
from app.routers import health

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "Starting mundial-ko-api | region=%s dynamo_endpoint=%s",
        settings.AWS_REGION,
        settings.DYNAMODB_ENDPOINT_URL or "AWS default",
    )
    yield


app = FastAPI(title="mundial-ko-api", lifespan=lifespan)
app.add_middleware(AuthMiddleware)
app.include_router(health.router)
