import time
import redis.asyncio as redis
from aiogram import BaseMiddleware
from aiogram.types import Update
from typing import Any, Callable, Dict, Awaitable
from src.config import settings
import logging

logger = logging.getLogger("datatap.throttling")


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, redis_client: redis.Redis, limit: int = 10, window: int = 1):
        self.redis = redis_client
        self.limit = limit
        self.window = window

    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any],
    ) -> Any:
        if not event.from_user:
            return await handler(event, data)

        user_id = event.from_user.id
        key = f"rate:{user_id}"
        now = time.time()
        window_start = now - self.window

        async with self.redis.pipeline() as pipe:
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zadd(key, {str(now): now})
            pipe.zcard(key)
            pipe.expire(key, self.window + 1)
            _, _, count, _ = await pipe.execute()

        if count > self.limit:
            logger.warning(f"⚠️ Rate limit hit for user {user_id}")
            return None
        return await handler(event, data)
