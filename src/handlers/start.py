from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from src.database.session import async_session_factory
from src.database.repository import create_user, get_user_by_tg_id
from src.keyboards.inline import get_main_menu

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    ref_code = message.text.split()[-1] if len(message.text.split()) > 1 else None
    async with async_session_factory() as session:
        user = await get_user_by_tg_id(session, message.from_user.id)
        if not user:
            user = await create_user(
                session,
                message.from_user.id,
                message.from_user.username,
                message.from_user.first_name,
                ref_code,
            )
            await session.commit()
        else:
            await session.refresh(user)

        await message.answer(
            f"👋 Добро пожаловать в DataTap, {message.from_user.first_name}!\n\n"
            f"💼 Баланс: {int(user.balance)} DATS\n⚡ Энергия: {user.energy}/{user.max_energy}\n\n"
            f"Нажимай 💻 ТАП! и развивай дата-центр.",
            reply_markup=get_main_menu(),
        )
