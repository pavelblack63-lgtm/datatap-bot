#!/bin/bash
# DataTap Bot - Single Deploy Script
# Запусти на VPS через PuTTY

set -e

BOT_DIR="/root/datatap-bot"

echo "=== DataTap Bot Deploy ==="

# Install Docker if needed
if ! command -v docker &> /dev/null; then
    echo "Установка Docker..."
    apt update && apt install -y docker.io docker-compose
fi

# Create directory
mkdir -p $BOT_DIR
cd $BOT_DIR

# Create docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: ${DB_USER:-datatap}
      POSTGRES_PASSWORD: ${DB_PASS:-secure_password}
      POSTGRES_DB: ${DB_NAME:-datatap}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-datatap}"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  bot:
    build: .
    env_file:
      - .env
    volumes:
      - ./logs:/app/logs
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

volumes:
  postgres_data:
EOF

# Create Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY .env.example ./

ENV PYTHONPATH=/app

CMD ["python", "-m", "src.main"]
EOF

# Create requirements.txt
cat > requirements.txt << 'EOF'
aiogram==3.4.1
sqlalchemy[asyncio]==2.0.35
asyncpg==0.29.0
redis==5.0.0
pydantic-settings==2.3.4
python-dotenv==1.0.1
aiohttp==3.9.5
EOF

# Create .env
cat > .env << 'EOF'
# Telegram
BOT_TOKEN=YOUR_TOKEN_HERE
ADMIN_IDS=YOUR_ID

# Database
DB_USER=datatap
DB_PASS=secure_password
DB_NAME=datatap
DATABASE_URL=postgresql+asyncpg://datatap:secure_password@postgres:5432/datatap
REDIS_URL=redis://redis:6379/0

# Security
SECRET_KEY=change_this_to_random_string_at_least_32_chars

# Game Balance
START_BALANCE=500
START_ENERGY=1000
MAX_ENERGY=1000
ENERGY_RESTORE_SEC=3
TAP_COOLDOWN_MS=100
REFERRAL_BONUS_FIXED=50
REFERRAL_BONUS_PERCENT=0.05

LOG_LEVEL=INFO
EOF

# Create logs dir
mkdir -p logs

# Create src structure
mkdir -p $BOT_DIR/src/{database,services,handlers,keyboards,middlewares,utils}

# Create all src files (simplified versions)
cat > $BOT_DIR/src/__init__.py << 'EOF'
"""DataTap Bot"""
EOF

cat > $BOT_DIR/src/config.py << 'EOF'
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    BOT_TOKEN: str = ""
    ADMIN_IDS: list[int] = []
    DATABASE_URL: str = "postgresql+asyncpg://datatap:pass@postgres:5432/datatap"
    REDIS_URL: str = "redis://redis:6379/0"
    SECRET_KEY: str = ""
    START_BALANCE: float = 500
    START_ENERGY: int = 1000
    MAX_ENERGY: int = 1000
    ENERGY_RESTORE_SEC: int = 3
    TAP_COOLDOWN_MS: int = 100
    REFERRAL_BONUS_FIXED: float = 50
    REFERRAL_BONUS_PERCENT: float = 0.05
    LOG_LEVEL: str = "INFO"

settings = Settings()
EOF

cat > $BOT_DIR/src/main.py << 'EOF'
import asyncio, logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from src.config import settings
from src.database.session import engine

async def on_startup():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logging.info("Starting DataTap Bot...")
    from src.database.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    from src.database.session import get_redis_or_fake
    r = await get_redis_or_fake()
    await r.ping()
    logging.info("Database connected")

async def main():
    await on_startup()
    bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(__import__('src.handlers.start', fromlist=['router']).router)
    dp.include_router(__import__('src.handlers.tap', fromlist=['router']).router)
    dp.include_router(__import__('src.handlers.upgrades', fromlist=['router']).router)
    dp.include_router(__import__('src.handlers.profile', fromlist=['router']).router)
    logging.info("Bot polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
EOF

# Create database files
cat > $BOT_DIR/src/database/__init__.py << 'EOF'
from .models import Base, User, Upgrade
from .session import engine, async_session_maker
EOF

cat > $BOT_DIR/src/database/models.py << 'EOF'
from datetime import datetime
from sqlalchemy import String, BigInteger, Integer, Numeric, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase): pass

class User(Base):
    __tablename__ = "users"
    tg_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    referral_code: Mapped[str] = mapped_column(String(12), unique=True)
    referred_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.tg_id"), nullable=True)
    balance: Mapped[float] = mapped_column(Numeric(20, 2), default=500)
    energy: Mapped[int] = mapped_column(Integer, default=1000)
    max_energy: Mapped[int] = mapped_column(Integer, default=1000)
    last_energy_update: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_tap_timestamp: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    tap_power: Mapped[int] = mapped_column(Integer, default=1)
    passive_income: Mapped[float] = mapped_column(Numeric(20, 4), default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Upgrade(Base):
    __tablename__ = "upgrades"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str] = mapped_column(String(255))
    price: Mapped[float] = mapped_column(Numeric(20, 2))
    tap_power_bonus: Mapped[int] = mapped_column(Integer, default=0)
    max_energy_bonus: Mapped[int] = mapped_column(Integer, default=0)
    passive_income_bonus: Mapped[float] = mapped_column(Numeric(20, 4), default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class UserUpgrade(Base):
    __tablename__ = "user_upgrades"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_tg_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.tg_id"))
    upgrade_id: Mapped[int] = mapped_column(Integer, ForeignKey("upgrades.id"))
    purchased_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
EOF

cat > $BOT_DIR/src/database/session.py << 'EOF'
from contextlib import asynccontextmanager
import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from src.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False, pool_pre_ping=True)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

_redis = None
class SimpleCache:
    def __init__(self): self._d = {}
    async def get(self, k): return self._d.get(k)
    async def set(self, k, v, ex=None): self._d[k] = v
    async def incr(self, k): self._d[k] = str(int(self._d.get(k,"0"))+1; return int(self._d[k])
    async def expire(self, k, s): pass
    async def pipeline(self): return self
    async def ping(self): return True

async def get_redis_or_fake():
    global _redis
    if _redis is None:
        try:
            _redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            await _redis.ping()
        except: _redis = SimpleCache()
    return _redis

async def get_session():
    async with async_session_maker() as s: yield s
EOF

cat > $BOT_DIR/src/database/repository.py << 'EOF'
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .models import User, Upgrade, UserUpgrade

class UserRepository:
    def __init__(self, session): self.session = session
    async def get_user(self, tg_id):
        r = await self.session.execute(select(User).where(User.tg_id == tg_id))
        return r.scalar_one_or_none()
    async def create_user(self, tg_id, username=None, referred_by=None):
        from src.config import settings
        import uuid
        user = User(tg_id=tg_id, username=username, referred_by=referred_by,
            balance=settings.START_BALANCE, energy=settings.START_ENERGY,
            max_energy=settings.MAX_ENERGY, referral_code=uuid.uuid4().hex[:8].upper())
        self.session.add(user); await self.session.commit(); return user
    async def get_referral_by_code(self, code):
        r = await self.session.execute(select(User).where(User.referral_code == code))
        return r.scalar_one_or_none()
    async def get_referrals(self, tg_id):
        r = await self.session.execute(select(User).where(User.referred_by == tg_id))
        return list(r.scalars().all())

class UpgradeRepository:
    def __init__(self, session): self.session = session
    async def get_all_active(self):
        r = await self.session.execute(select(Upgrade).where(Upgrade.is_active == True))
        return list(r.scalars().all())
    async def get_upgrade(self, id):
        r = await self.session.execute(select(Upgrade).where(Upgrade.id == id))
        return r.scalar_one_or_none()
    async def has_upgrade(self, tg_id, upgrade_id):
        r = await self.session.execute(select(UserUpgrade).where(
            UserUpgrade.user_tg_id == tg_id, UserUpgrade.upgrade_id == upgrade_id))
        return r.scalar_one_or_none() is not None
EOF

# Create handlers
cat > $BOT_DIR/src/handlers/__init__.py << 'EOF'
EOF

cat > $BOT_DIR/src/handlers/start.py << 'EOF'
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from src.database.session import async_session_maker
from src.database.repository import UserRepository
from src.keyboards.inline import get_start_keyboard

router = Router()

@router.message(CommandStart())
async def handle_start(message: Message):
    tg_id = message.from_user.id
    username = message.from_user.username
    referrer = None
    
    if message.command and message.command.args and message.command.args.startswith("ref_"):
        code = message.command.args[4:]
        async with async_session_maker() as s:
            repo = UserRepository(s)
            referrer = await repo.get_referral_by_code(code)
    
    async with async_session_maker() as s:
        repo = UserRepository(s)
        user = await repo.get_user(tg_id)
        if not user:
            user = await repo.create_user(tg_id, username, referrer.tg_id if referrer else None)
            if referrer:
                from src.config import settings
                ref_user = await repo.get_user(referrer.tg_id)
                ref_user.balance += settings.REFERRAL_BONUS_FIXED
                await s.commit()
    
    ref_link = f"t.me/DataTapBot?start=ref_{user.referral_code}"
    await message.answer(f"🏢 <b>DataTap!</b>\n\n💰 Баланс: <b>{user.balance:.2f}</b>\n⚡ Энергия: <b>{user.energy}/{user.max_energy}</b>\n👆 Сила: <b>{user.tap_power}</b>\n📥 Пассив: <b>{user.passive_income:.4f}/мин</b>\n\n🔗 {ref_link}", reply_markup=get_start_keyboard())
EOF

cat > $BOT_DIR/src/handlers/tap.py << 'EOF'
from aiogram import Router, F
from aiogram.types import CallbackQuery
from src.database.session import async_session_maker
from src.services.tap_service import TapService
from src.keyboards.inline import get_tap_keyboard

router = Router()

@router.callback_query(F.data == "tap")
async def handle_tap(callback: CallbackQuery):
    tg_id = callback.from_user.id
    async with async_session_maker() as s:
        svc = TapService(s)
        result = await svc.process_tap(tg_id)
    if result.get("success"):
        await callback.message.edit_text(f"💻 <b>Тап!</b>\n\n💰 {result['balance']:.2f}\n⚡ {result['energy']}/{result.get('max_energy',1000)}\n👆 {result['tap_power']}", reply_markup=get_tap_keyboard())
    else:
        await callback.answer(result.get("error","Ошибка"), show_alert=True)
    await callback.answer()
EOF

cat > $BOT_DIR/src/handlers/upgrades.py << 'EOF'
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from src.database.session import async_session_maker
from src.services.upgrade_service import UpgradeService
from src.keyboards.inline import get_upgrades_keyboard

router = Router()

@router.message(Command("upgrades"))
async def show_upgrades(message: Message):
    tg_id = message.from_user.id
    async with async_session_maker() as s:
        svc = UpgradeService(s)
        ups = await svc.get_available_upgrades(tg_id)
    text = "🛒 <b>Магазин</b>\n\n"
    for u in ups: text += f"{u['name']}: {'✅' if u['owned'] else f'💰 {u[\"price\"]:.0f}'}\n{u['description']}\n\n"
    await message.answer(text, reply_markup=get_upgrades_keyboard(ups))

@router.callback_query(F.data.startswith("buy_upgrade_"))
async def buy_upgrade(callback: CallbackQuery):
    tg_id = callback.from_user.id
    upgrade_id = int(callback.data.split("_")[-1])
    async with async_session_maker() as s:
        svc = UpgradeService(s)
        result = await svc.purchase_upgrade(tg_id, upgrade_id)
    if result.get("success"):
        await callback.message.edit_text(f"✅ Куплено: {result['name']}\n💰 {result['new_balance']:.2f}")
    else:
        await callback.answer(result.get("error","Ошибка"), show_alert=True)
    await callback.answer()
EOF

cat > $BOT_DIR/src/handlers/profile.py << 'EOF'
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from src.database.session import async_session_maker
from src.database.repository import UserRepository
from src.keyboards.inline import get_profile_keyboard

router = Router()

@router.message(Command("profile"))
async def show_profile(message: Message):
    tg_id = message.from_user.id
    async with async_session_maker() as s:
        repo = UserRepository(s)
        user = await repo.get_user(tg_id)
        refs = await repo.get_referrals(tg_id)
    e_bar = "█"*(user.energy*10//user.max_energy)+"░"*(10-user.energy*10//user.max_energy)
    await message.answer(f"👤 <b>Профиль</b>\n\n🆔 {user.tg_id}\n📛 @{user.username or 'N/A'}\n💰 {user.balance:.2f}\n⚡ {user.energy}/{user.max_energy} [{e_bar}]\n👆 {user.tap_power}\n📥 {user.passive_income:.4f}/мин\n👥 Рефералов: {len(refs)}", reply_markup=get_profile_keyboard())
EOF

# Create services
cat > $BOT_DIR/src/services/__init__.py << 'EOF'
EOF

cat > $BOT_DIR/src/services/tap_service.py << 'EOF'
from datetime import datetime
from src.database.repository import UserRepository

class TapService:
    def __init__(self, session): self.session = session; self.repo = UserRepository(session)
    async def process_tap(self, tg_id):
        user = await self.repo.get_user(tg_id)
        if not user: return {"success": False, "error": "Нет пользователя"}
        if user.last_tap_timestamp:
            diff = (datetime.utcnow() - user.last_tap_timestamp).total_seconds() * 1000
            if diff < 100: return {"success": False, "error": "Слишком быстро"}
        if user.energy <= 0: return {"success": False, "error": "Нет энергии"}
        user.balance += user.tap_power
        user.energy -= 1
        user.last_tap_timestamp = datetime.utcnow()
        await self.session.commit()
        return {"success": True, "balance": user.balance, "energy": user.energy, "tap_power": user.tap_power, "max_energy": user.max_energy}
EOF

cat > $BOT_DIR/src/services/upgrade_service.py << 'EOF'
from src.database.repository import UserRepository, UpgradeRepository
from src.database.models import Upgrade

class UpgradeService:
    def __init__(self, session):
        self.session = session
        self.user_repo = UserRepository(session)
        self.upgrade_repo = UpgradeRepository(session)
    async def get_available_upgrades(self, tg_id):
        ups = await self.upgrade_repo.get_all_active()
        user = await self.user_repo.get_user(tg_id)
        r = []
        for u in ups:
            has = await self.upgrade_repo.has_upgrade(tg_id, u.id)
            r.append({"id": u.id, "name": u.name, "description": u.description, "price": float(u.price),
                "tap_power_bonus": u.tap_power_bonus, "max_energy_bonus": u.max_energy_bonus,
                "passive_income_bonus": float(u.passive_income_bonus), "owned": has,
                "can_afford": user.balance >= u.price})
        return r
    async def purchase_upgrade(self, tg_id, upgrade_id):
        upg = await self.upgrade_repo.get_upgrade(upgrade_id)
        if not upg: return {"success": False, "error": "Не найдено"}
        if await self.upgrade_repo.has_upgrade(tg_id, upgrade_id): return {"success": False, "error": "Уже есть"}
        user = await self.user_repo.get_user(tg_id)
        if user.balance < upg.price: return {"success": False, "error": "Недостаточно"}
        user.balance -= upg.price
        if upg.tap_power_bonus: user.tap_power += upg.tap_power_bonus
        if upg.max_energy_bonus: user.max_energy += upg.max_energy_bonus
        if upg.passive_income_bonus: user.passive_income += upg.passive_income_bonus
        from .models import UserUpgrade
        self.session.add(UserUpgrade(user_tg_id=tg_id, upgrade_id=upgrade_id))
        await self.session.commit()
        return {"success": True, "name": upg.name, "new_balance": float(user.balance),
            "tap_power": user.tap_power, "max_energy": user.max_energy, "passive_income": float(user.passive_income)}
    async def seed_default_upgrades(self):
        defaults = [
            {"name": "SSD Drive", "description": "+1 к силе тапа", "price": 100, "tap_power_bonus": 1},
            {"name": "Cooling Fan", "description": "+50 макс. энергии", "price": 500, "max_energy_bonus": 50},
            {"name": "Backup PSU", "description": "+0.1 DATS/мин", "price": 2000, "passive_income_bonus": 0.1}
        ]
        for d in defaults:
            if not await self.upgrade_repo.get_upgrade(d["name"]):
                self.session.add(Upgrade(**d))
        await self.session.commit()
EOF

# Create keyboards
cat > $BOT_DIR/src/keyboards/__init__.py << 'EOF'
EOF

cat > $BOT_DIR/src/keyboards/inline.py << 'EOF'
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def get_start_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💻 Тап", callback_data="tap")],
        [InlineKeyboardButton(text="🛒 Улучшения", callback_data="show_upgrades"),
         InlineKeyboardButton(text="👤 Профиль", callback_data="show_profile")]
    ])

def get_tap_keyboard(): return get_start_keyboard()

def get_upgrades_keyboard(upgrades):
    btns = [[InlineKeyboardButton(text=f"💰 {u['name']} ({u['price']:.0f})", callback_data=f"buy_upgrade_{u['id']}")]
            for u in upgrades if not u['owned']]
    btns.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=btns)

def get_profile_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💻 Тап", callback_data="tap")],
        [InlineKeyboardButton(text="🛒 Улучшения", callback_data="show_upgrades"),
         InlineKeyboardButton(text="👥 Рефералы", callback_data="show_referrals")]
    ])
EOF

# Create middlewares (empty for now)
cat > $BOT_DIR/src/middlewares/__init__.py << 'EOF'
EOF

# Create utils
cat > $BOT_DIR/src/utils/__init__.py << 'EOF'
EOF

echo "=== Файлы созданы ==="
echo "Теперь:"
echo "1. Добавь BOT_TOKEN в .env"
echo "2. docker-compose up -d --build"
echo "3. docker-compose logs -f bot"