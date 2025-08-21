#!/usr/bin/env python3
"""
FinFlow - Управление проектом
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Выполнение команды с описанием"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} завершено успешно")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка при {description.lower()}: {e}")
        if e.stderr:
            print(f"Детали ошибки: {e.stderr}")
        return False

def main():
    """Главная функция управления"""
    print("🎯 FinFlow - Управление проектом")
    print("=" * 50)
    
    while True:
        print("\nВыберите действие:")
        print("1. Запустить Django сервер")
        print("2. Запустить Telegram бота")
        print("3. Создать миграции")
        print("4. Применить миграции")
        print("5. Создать суперпользователя")
        print("6. Проверить проект")
        print("7. Установить зависимости")
        print("0. Выход")
        
        choice = input("\nВведите номер действия: ").strip()
        
        if choice == "1":
            print("\n🚀 Запуск Django сервера...")
            print("Сервер будет доступен по адресу: http://127.0.0.1:8000/")
            print("Для остановки нажмите Ctrl+C")
            subprocess.run("python manage.py runserver", shell=True)
            
        elif choice == "2":
            print("\n🤖 Запуск Telegram бота...")
            print("Для остановки нажмите Ctrl+C")
            subprocess.run("python run_bot.py", shell=True)
            
        elif choice == "3":
            run_command("python manage.py makemigrations", "Создание миграций")
            
        elif choice == "4":
            run_command("python manage.py migrate", "Применение миграций")
            
        elif choice == "5":
            print("\n👤 Создание суперпользователя...")
            subprocess.run("python manage.py createsuperuser", shell=True)
            
        elif choice == "6":
            run_command("python manage.py check", "Проверка проекта")
            
        elif choice == "7":
            run_command("pip install -r requirements.txt", "Установка зависимостей")
            
        elif choice == "0":
            print("\n👋 До свидания!")
            break
            
        else:
            print("❌ Неверный выбор. Попробуйте снова.")

if __name__ == "__main__":
    main()
