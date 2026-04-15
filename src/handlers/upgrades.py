from aiogram import Router, F
from aiogram.types import CallbackQuery
from src.database.session import async_session_factory
from src.database.repository import get_user_by_tg_id
from src.services.upgrade_service import purchase_upgrade, UPGRADES_CONFIG, get_upgrade_cost
from src.keyboards.inline import get_upgrades, get_main_menu, get_back

router = Router()


@router.callback_query(F.data == "upgrades")
async def show_shop(cb: CallbackQuery):
    await cb.message.edit_text("🛒 Выберите улучшение:", reply_markup=get_upgrades())


@router.callback_query(F.data.startswith("buy_"))
async def buy_item(cb: CallbackQuery):
    utype = cb.data.replace("buy_", "")
    async with async_session_factory() as session:
        user = await get_user_by_tg_id(session, cb.from_user.id)
        if not user:
            return await cb.answer("⚠️ Сначала /start", show_alert=True)

        res = await purchase_upgrade(session, user, utype)
        await session.commit()
        await cb.answer(res["message"], show_alert=True)

        if res["success"]:
            cfg = UPGRADES_CONFIG[utype]
            await cb.message.edit_text(
                f"✅ `{cfg['name']}` куплен!\n💼 Остаток: `{int(res['new_balance'])}`\n📊 Уровень: `{res['new_level']}`",
                parse_mode="Markdown",
                reply_markup=get_main_menu(),
            )


@router.callback_query(F.data == "main_menu")
async def back_menu(cb: CallbackQuery):
    async with async_session_factory() as session:
        user = await get_user_by_tg_id(session, cb.from_user.id)
        if user:
            await cb.message.edit_text(
                f"💼 {int(user.balance)} DATS | ⚡ {user.energy}/{user.max_energy}",
                reply_markup=get_main_menu(),
            )
