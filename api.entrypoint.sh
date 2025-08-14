#!/usr/bin/zsh
set -e

export PYTHONPATH=/app
DEBUG=false

while getopts "d" opt; do
  case $opt in
    d) DEBUG=true ;;
    *) echo "❌ Неверный параметр"; exit 1 ;;
  esac
done

echo "🔄 Выполняем миграции..."
touch lots.db
poetry env activate
poetry run alembic upgrade head

echo "🚀 Запускаем API..."
exec poetry run python api/main.py
