#!/bin/bash
# DataTap Bot - Quick Deploy Script

set -e

echo "=== DataTap Bot Deploy ==="

# Get bot files
echo "Способ загрузки файлов:"
echo "1 - Git clone (если есть репозиторий)"
echo "2 - Скачать архив"
read -p "Выбери (1/2): " method

if [ "$method" = "1" ]; then
    echo "Введи URL репозитория:"
    read repo_url
    git clone "$repo_url" datatap-bot
    cd datatap-bot
elif [ "$method" = "2" ]; then
    mkdir -p datatap-bot
    cd datatap-bot
    echo "Загрузи файлы проекта в эту папку"
fi

# Create logs directory
mkdir -p logs

# Create .env file
if [ ! -f .env ]; then
    echo "Создаю .env..."
    cat > .env << 'EOF'
# Telegram
BOT_TOKEN=
ADMIN_IDS=

# Database
DB_USER=datatap
DB_PASS=secure_password
DB_NAME=datatap
DATABASE_URL=postgresql+asyncpg://datatap:secure_password@postgres:5432/datatap
REDIS_URL=redis://redis:6379/0

# Security
SECRET_KEY=change_this_to_random_long_string_min_32_chars
WEBHOOK_URL=

# Game Balance
START_BALANCE=500
START_ENERGY=1000
MAX_ENERGY=1000
ENERGY_RESTORE_SEC=3
TAP_COOLDOWN_MS=100
REFERRAL_BONUS_FIXED=50
REFERRAL_BONUS_PERCENT=0.05
EOF
    echo "Отредактируй .env и добавь BOT_TOKEN"
fi

# Build and start
echo "Собираем и запускаем..."
docker-compose up -d --build

echo ""
echo "=== Готово! ==="
echo "Статус: docker-compose ps"
echo "Логи бота: docker-compose logs -f bot"
echo "Логи ошибки: docker-compose logs -f bot | grep -i error"
echo ""
echo "После добавления BOT_TOKEN перезапусти: docker-compose restart bot"