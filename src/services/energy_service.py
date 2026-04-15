from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from src.database.models import User
from src.config import settings
import math


async def calculate_current_energy(user: User) -> int:
    now = datetime.utcnow()
    last = user.last_energy_update or now
    elapsed_sec = (now - last).total_seconds()
    restored = math.floor(elapsed_sec / settings.ENERGY_RESTORE_SEC)
    if restored > 0:
        return min(user.energy + restored, user.max_energy)
    return user.energy


async def restore_energy(session: AsyncSession, user: User) -> int:
    current = await calculate_current_energy(user)
    if current != user.energy:
        await session.execute(
            update(User)
            .where(User.id == user.id)
            .values(energy=current, last_energy_update=datetime.utcnow())
        )
        return current
    return user.energy
