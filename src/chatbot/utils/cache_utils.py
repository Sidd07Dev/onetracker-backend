from ..config.redis import RedisClient
import json

class CacheUtils:

    @staticmethod
    async def set(key: str, value: dict, expire: int = 300):
        client = await RedisClient.get_client()
        await client.set(key, json.dumps(value), ex=expire)

    @staticmethod
    async def get(key: str):
        client = await RedisClient.get_client()
        data = await client.get(key)
        if data:
            return json.loads(data)
        return None

    @staticmethod
    async def delete(key: str):
        client = await RedisClient.get_client()
        await client.delete(key)
