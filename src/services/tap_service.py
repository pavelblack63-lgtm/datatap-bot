from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models import User
from src.config import settings
from src.services.energy_service import restore_energy
import logging

logger = logging.getLogger("datatap.tap")


async def process_tap(session: AsyncSession, user: User) -> dict:
    user.energy = await restore_energy(session, user)
    await session.flush()

    if user.energy <= 0:
        return {"success": False, "message": "⚡ Нет энергии! Подожди восстановления."}

    if user.last_tap_timestamp:
        elapsed_ms = (datetime.utcnow() - user.last_tap_timestamp).total_seconds() * 1000
        if elapsed_ms < settings.TAP_COOLDOWN_MS:
            return {"success": False, "message": "⏳ Слишком быстро! Не спамь кликами."}

    now = datetime.utcnow()
    reward = user.tap_power
    user.balance += reward
    user.energy -= 1
    user.last_tap_timestamp = now
    await session.flush()

    logger.debug(f"Tap: user={user.tg_id} +{reward} bal={user.balance} eng={user.energy}")
    return {"success": True, "reward": reward, "balance": user.balance, "energy": user.energy}
