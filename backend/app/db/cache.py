import redis.asyncio as aioredis

from app.config import settings
from app.logging import get_logger

logger = get_logger("cache")

_client: aioredis.Redis | None = None


async def connect() -> None:
    global _client
    _client = aioredis.Redis(
        host=settings.REDIS_ENDPOINT,
        port=settings.REDIS_PORT,
        decode_responses=True,
        socket_timeout=5,
        socket_connect_timeout=5,
    )
    await _client.ping()
    logger.info("cache_connected", host=settings.REDIS_ENDPOINT, port=settings.REDIS_PORT)


async def disconnect() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
        logger.info("cache_disconnected")


def get_cache() -> aioredis.Redis:
    if _client is None:
        raise RuntimeError("Cache client is not connected. Call connect() first.")
    return _client
