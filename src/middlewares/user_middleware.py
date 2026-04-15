from aiogram import BaseMiddleware
from aiogram.types import Update
from typing import Any, Callable, Dict, Awaitable
from src.database.session import async_session_factory
from src.database.repository import get_user_by_tg_id
from src.services.energy_service import restore_energy
import logging

logger = logging.getLogger("datatap.user_mw")


class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any],
    ) -> Any:
        if not event.from_user:
            return await handler(event, data)

        async with async_session_factory() as session:
            user = await get_user_by_tg_id(session, event.from_user.id)
            if user:
                await restore_energy(session, user)
                await session.commit()
        return await handler(event, data)
