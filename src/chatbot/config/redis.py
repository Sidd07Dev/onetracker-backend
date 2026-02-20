import redis.asyncio as redis
from typing import Optional
import os


REDIS_URL = os.getenv("REDIS_URI", "redis://redis:6379/0")


class RedisClient:
    _client: Optional[redis.Redis] = None

    @classmethod
    async def get_client(cls) -> redis.Redis:
        if cls._client is None:
            cls._client = redis.from_url(
                REDIS_URL,
                decode_responses=True
            )
        return cls._client