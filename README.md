# DataTap — Telegram Clicker Game

Telegram-бот в жанре tap-to-earn с дата-центром тематикой. Аналог Hamster Kombat.

## 🚀 Быстрый старт

### 1. Клонирование и настройка
```bash
git clone <repo-url>
cd datatap-bot
cp .env.example .env
```

### 2. Настройка .env
Отредактируйте `.env`:
- `BOT_TOKEN` — получите у @BotFather
- `SECRET_KEY` — сгенерируйте случайную строку (32+ символа)

### 3. Запуск через Docker
```bash
docker-compose up --build
```

### 4. Запуск без Docker
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac
pip install -e .
python -m src.main
```

## 🎮 Команды бота

- `/start` — начать игру, получить реферальную ссылку
- `/profile` — профиль игрока
- `/upgrades` — магазин улучшений
- `/referrals` — реферальная программа
- `💻 Тап` — клик для заработка

## 🏗️ Архитектура

- **aiogram 3.x** — асинхронный фреймворк бота
- **SQLAlchemy 2.x (async)** — работа с PostgreSQL
- **Redis** — кеширование, rate-limit, восстановление энергии
- **pydantic-settings** — конфигурация через .env

## 📝 Лицензия

MIT