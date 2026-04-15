from aiogram import Router, F
from aiogram.types import CallbackQuery
from src.database.session import async_session_factory
from src.database.repository import get_user_by_tg_id
from src.keyboards.inline import get_back
from src.services.energy_service import calculate_current_energy

router = Router()


@router.callback_query(F.data == "profile")
async def show_profile(cb: CallbackQuery):
    async with async_session_factory() as session:
        user = await get_user_by_tg_id(session, cb.from_user.id)
        if not user:
            return await cb.answer("⚠️ Сначала /start", show_alert=True)

        energy = calculate_current_energy(user)
        text = (
            f"👤 *Профиль*\n\n"
            f"💼 Баланс: `{int(user.balance)}` DATS\n⚡ Энергия: `{energy}` / `{user.max_energy}`\n"
            f"👆 Сила клика: `{user.tap_power}`\n📈 Пассив: `{user.passive_income}`/мин\n\n"
            f"🔗 Реф. код: `{user.referral_code}`"
        )
        await cb.message.edit_text(text, parse_mode="Markdown", reply_markup=get_back())
