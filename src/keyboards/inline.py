from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_main_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row({"text": "💻 ТАП!", "callback_data": "tap"})
    kb.row(
        {"text": "📈 Магазин", "callback_data": "upgrades"},
        {"text": "👤 Профиль", "callback_data": "profile"},
    )
    return kb.as_markup()


def get_upgrades() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row({"text": "💾 SSD Drive", "callback_data": "buy_ssd"})
    kb.row({"text": "❄️ Cooling Fan", "callback_data": "buy_cooling"})
    kb.row({"text": "🔋 Backup PSU", "callback_data": "buy_psu"})
    kb.row({"text": "🔙 Назад", "callback_data": "main_menu"})
    return kb.as_markup()


def get_back() -> InlineKeyboardMarkup:
    return (
        InlineKeyboardBuilder().row({"text": "🔙 Назад", "callback_data": "main_menu"}).as_markup()
    )
