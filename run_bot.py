#!/usr/bin/env python3
"""
FinFlow - Запуск Telegram бота
"""

import os
import sys
import django
from pathlib import Path

# Добавляем корневую директорию проекта в Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# Настраиваем Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# Импортируем и запускаем бота
from bot.bot import main
import asyncio

if __name__ == "__main__":
    print("🚀 Запуск FinFlow Telegram Bot...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")
        sys.exit(1)
