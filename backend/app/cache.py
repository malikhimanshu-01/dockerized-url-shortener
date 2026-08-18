import time

import redis.asyncio as redis

from app.config import settings

redis_client = redis.Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    decode_responses=True,
)

REDIRECT_CACHE_TTL_SECONDS = 60 * 60 * 24  # 24h, per section 6


async def get_cached_long_url(short_code: str) -> str | None:
    return await redis_client.get(f"link:{short_code}")


async def cache_long_url(short_code: str, long_url: str) -> None:
    await redis_client.set(f"link:{short_code}", long_url, ex=REDIRECT_CACHE_TTL_SECONDS)


async def invalidate_cached_url(short_code: str) -> None:
    await redis_client.delete(f"link:{short_code}")


async def check_rate_limit(identifier: str, limit: int, window_seconds: int) -> bool:
    """Fixed-window counter: INCR + EXPIRE on ratelimit:{identifier}:{window_bucket}.

    Returns True if the request is allowed under the limit.
    """
    bucket = int(time.time() // window_seconds)
    key = f"ratelimit:{identifier}:{bucket}"
    count = await redis_client.incr(key)
    if count == 1:
        await redis_client.expire(key, window_seconds)
    return count <= limit
