"""
NEXUS Redis Client & Connection Pool Manager
Provides async connection pooling, stream initialization, and resilient fallback.
"""

from typing import Optional
import redis.asyncio as aioredis
import logging

from configs.settings import settings

logger = logging.getLogger("nexus.redis")


class RedisManager:
    def __init__(self):
        self._pool: Optional[aioredis.ConnectionPool] = None
        self._client: Optional[aioredis.Redis] = None
        self._is_available: bool = False

    async def initialize(self) -> bool:
        try:
            self._pool = aioredis.ConnectionPool(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                password=settings.redis_password,
                decode_responses=True,
                max_connections=50,
            )
            self._client = aioredis.Redis(connection_pool=self._pool)
            await self._client.ping()
            self._is_available = True
            logger.info("Connected to Redis successfully.")
            return True
        except Exception as e:
            logger.warning(f"Could not connect to Redis at {settings.redis_host}:{settings.redis_port} ({e}). Running in decoupled/mock mode.")
            self._is_available = False
            return False

    @property
    def client(self) -> Optional[aioredis.Redis]:
        return self._client

    @property
    def is_available(self) -> bool:
        return self._is_available

    async def close(self):
        if self._client:
            await self._client.close()
        if self._pool:
            await self._pool.disconnect()
        self._is_available = False


redis_manager = RedisManager()
