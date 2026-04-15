import asyncio
import logging
from sqlalchemy import select, update
from src.database.session import async_session_factory
from src.database.models import User
import logging

logger = logging.getLogger("datatap.passive")


async def passive_income_worker(interval_sec: int = 60):
    """Фоновая задача: начисляет пассивный доход каждую минуту."""
    logger.info("🔄 Passive income worker started")
    while True:
        try:
            async with async_session_factory() as session:
                result = await session.execute(
                    select(User.id, User.balance, User.passive_income).where(
                        User.is_active == True, User.passive_income > 0
                    )
                )
                users = result.all()

                if not users:
                    await asyncio.sleep(interval_sec)
                    continue

                for user_id, balance, passive in users:
                    income = float(passive)
                    await session.execute(
                        update(User).where(User.id == user_id).values(balance=balance + income)
                    )
                await session.commit()
                logger.debug(f"✅ Processed passive income for {len(users)} users")

        except Exception as e:
            logger.error(f"💥 Passive income worker error: {e}")
            await asyncio.sleep(5)

        await asyncio.sleep(interval_sec)
