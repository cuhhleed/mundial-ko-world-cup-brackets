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


_MATCH_TTL = 86400  # 24 hours


async def set_match_state(match_id: str, match_data: dict) -> None:
    client = get_cache()
    key = f"match:{match_id}"
    await client.hset(key, mapping=match_data)
    await client.expire(key, _MATCH_TTL)


async def get_match_state(match_id: str) -> dict | None:
    client = get_cache()
    data = await client.hgetall(f"match:{match_id}")
    return data if data else None


async def set_round_matches(round_name: str, match_ids: list[str]) -> None:
    client = get_cache()
    key = f"round:{round_name}:matches"
    await client.delete(key)
    if match_ids:
        await client.rpush(key, *match_ids)
    await client.expire(key, _MATCH_TTL)
