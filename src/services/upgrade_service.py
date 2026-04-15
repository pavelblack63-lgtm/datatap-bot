from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models import User
from src.database.repository import get_user_upgrades, add_upgrade
from src.config import settings
import logging

logger = logging.getLogger("datatap.upgrade")

UPGRADES_CONFIG = {
    "ssd": {
        "name": "💾 SSD Drive",
        "base_cost": 100,
        "cost_mult": 1.5,
        "tap": 1,
        "energy": 0,
        "passive": 0,
    },
    "cooling": {
        "name": "❄️ Cooling Fan",
        "base_cost": 500,
        "cost_mult": 1.6,
        "tap": 0,
        "energy": 50,
        "passive": 0,
    },
    "psu": {
        "name": "🔋 Backup PSU",
        "base_cost": 2000,
        "cost_mult": 1.7,
        "tap": 0,
        "energy": 0,
        "passive": 0.1,
    },
}


def get_upgrade_cost(utype: str, level: int) -> int:
    cfg = UPGRADES_CONFIG[utype]
    return int(cfg["base_cost"] * (cfg["cost_mult"] ** level))


async def purchase_upgrade(session: AsyncSession, user: User, utype: str) -> dict:
    if utype not in UPGRADES_CONFIG:
        return {"success": False, "message": "❌ Неизвестное улучшение"}

    upgrades = await get_user_upgrades(session, user.id)
    current_level = next((u.level for u in upgrades if u.upgrade_type == utype), 0)
    cost = get_upgrade_cost(utype, current_level)

    if user.balance < cost:
        return {
            "success": False,
            "message": f"❌ Не хватает DATS! Нужно: {cost}, У вас: {int(user.balance)}",
        }

    cfg = UPGRADES_CONFIG[utype]
    user.balance -= cost
    user.tap_power += cfg["tap"]
    user.max_energy += cfg["energy"]
    user.passive_income += cfg["passive"]

    if current_level == 0:
        await add_upgrade(
            session,
            user.id,
            utype,
            level=1,
            bonus_tap=cfg["tap"],
            bonus_energy=cfg["energy"],
            bonus_passive=cfg["passive"],
        )
    else:
        for u in upgrades:
            if u.upgrade_type == utype:
                u.level += 1
                break

    await session.flush()
    logger.info(f"Upgrade: user={user.tg_id} type={utype} lv={current_level + 1}")
    return {
        "success": True,
        "new_balance": user.balance,
        "new_level": current_level + 1,
        "next_cost": get_upgrade_cost(utype, current_level + 1),
    }
