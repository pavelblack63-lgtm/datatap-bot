from aiogram import Router, F
from aiogram.types import CallbackQuery
from src.database.session import async_session_factory
from src.database.repository import get_user_by_tg_id
from src.services.tap_service import process_tap
from src.keyboards.inline import get_main_menu

router = Router()


@router.callback_query(F.data == "tap")
async def handle_tap(cb: CallbackQuery):
    async with async_session_factory() as session:
        user = await get_user_by_tg_id(session, cb.from_user.id)
        if not user:
            return await cb.answer("⚠️ Сначала /start", show_alert=True)

        res = await process_tap(session, user)
        await session.commit()

        if not res["success"]:
            return await cb.answer(res["message"], show_alert=True)

        await cb.answer(f"+{res['reward']} 💻")
        await cb.message.edit_text(
            f"💼 Баланс: {int(res['balance'])} DATS\n⚡ Энергия: {res['energy']}/{user.max_energy}",
            reply_markup=get_main_menu(),
        )
