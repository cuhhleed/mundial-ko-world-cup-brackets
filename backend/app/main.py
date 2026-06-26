from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.cache import connect as cache_connect
from app.db.cache import disconnect as cache_disconnect
from app.logging import configure_logging, get_logger
from app.routers import auth, brackets, health, leaderboard, matches, teams, users

configure_logging()
logger = get_logger("mundial-ko-api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "startup",
        region=settings.AWS_REGION,
        dynamo_endpoint=settings.DYNAMODB_ENDPOINT_URL or "AWS default",
    )
    await cache_connect()
    yield
    await cache_disconnect()


app = FastAPI(title="mundial-ko-api", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(brackets.router)
app.include_router(leaderboard.router)
app.include_router(matches.router)
app.include_router(teams.router)
