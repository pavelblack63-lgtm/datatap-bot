#!/bin/bash

echo "=== DataTap Bot Installation ==="

apt update && apt install -y docker.io docker-compose curl

echo "Создаём директорию..."
mkdir -p /root/datatap-bot
cd /root/datatap-bot

echo "Загружаем файлы..."
echo "Вставь сюда содержимое папки бота или используй git clone"

echo "Запускаем..."
docker-compose up -d --build

echo "Готово! Проверь статус: docker-compose ps"
echo "Логи: docker-compose logs -f bot"