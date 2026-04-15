from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from src.database.models import User, Upgrade
from src.utils.security import generate_referral_code
from src.config import settings
import logging

logger = logging.getLogger("datatap.repository")


async def get_user_by_tg_id(session: AsyncSession, tg_id: int) -> User | None:
    result = await session.execute(select(User).where(User.tg_id == tg_id))
    return result.scalar_one_or_none()


async def get_user_by_referral_code(session: AsyncSession, code: str) -> User | None:
    result = await session.execute(select(User).where(User.referral_code == code))
    return result.scalar_one_or_none()


async def create_user(
    session: AsyncSession,
    tg_id: int,
    username: str | None = None,
    first_name: str | None = None,
    referred_by_code: str | None = None,
) -> User:
    referral_code = generate_referral_code()
    referred_by_id = None

    if referred_by_code:
        referrer = await get_user_by_referral_code(session, referred_by_code)
        if referrer:
            referred_by_id = referrer.id
            logger.info(f"User {tg_id} registered via referral {referrer.tg_id}")

    new_user = User(
        tg_id=tg_id,
        username=username,
        first_name=first_name,
        referral_code=referral_code,
        referred_by=referred_by_id,
        balance=settings.START_BALANCE,
        energy=settings.START_ENERGY,
        max_energy=settings.MAX_ENERGY,
        tap_power=settings.TAP_POWER_BASE,
    )
    session.add(new_user)
    await session.flush()

    if referred_by_id:
        await session.execute(
            update(User)
            .where(User.id == referred_by_id)
            .values(balance=User.balance + settings.REFERRAL_BONUS_FIXED)
        )
        logger.info(f"Referral bonus {settings.REFERRAL_BONUS_FIXED} DATS -> user {referred_by_id}")

    return new_user


async def get_user_upgrades(session: AsyncSession, user_id: int) -> list[Upgrade]:
    result = await session.execute(select(Upgrade).where(Upgrade.user_id == user_id))
    return result.scalars().all()


async def add_upgrade(
    session: AsyncSession,
    user_id: int,
    upgrade_type: str,
    level: int = 1,
    bonus_tap: int = 0,
    bonus_energy: int = 0,
    bonus_passive: float = 0.0,
) -> Upgrade:
    upgrade = Upgrade(
        user_id=user_id,
        upgrade_type=upgrade_type,
        level=level,
        bonus_tap_power=bonus_tap,
        bonus_max_energy=bonus_energy,
        bonus_passive=bonus_passive,
    )
    session.add(upgrade)
    return upgrade
