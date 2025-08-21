# FinFlow - Автоматизированный финансовый ассистент для малого бизнеса

## Описание проекта

FinFlow - это интеллектуальный Telegram-бот, который помогает владельцам малого бизнеса анализировать расходы через фотографии чеков и предоставляет рекомендации по оптимизации бюджета. Система также поддерживает интеграцию с 1С для автоматизации учета.

## Основные возможности

- 📱 **Telegram-бот интерфейс** - удобное взаимодействие через мессенджер
- 🧾 **OCR распознавание чеков** - автоматическое извлечение данных из фотографий
- 📊 **Анализ расходов** - детальная аналитика и отчеты
- 💡 **Рекомендации по оптимизации** - AI-советы по сокращению затрат
- 🔗 **Интеграция с 1С** - синхронизация данных с системой учета
- 🖥️ **Админ-панель** - веб-интерфейс для управления и мониторинга

## Технологический стек

- **Backend**: Python 3.13, Django 5.0
- **Telegram Bot**: aiogram 3.22
- **OCR**: Tesseract + OpenCV
- **Анализ данных**: Pandas, NumPy
- **База данных**: PostgreSQL
- **Очереди задач**: Celery + Redis
- **Форматирование**: Black, isort, flake8

## Структура проекта

```
FinFlow/
├── bot/                    # Telegram бот
│   ├── bot.py             # Основная логика бота
│   ├── urls.py            # URL-маршруты для webhook
│   └── views.py           # Views для webhook
├── core/                   # Основная логика приложения
│   ├── services.py        # Бизнес-логика
│   └── models.py          # Импорт моделей
├── django_app/            # Django приложение
│   ├── models.py          # Модели данных
│   ├── views.py           # API views
│   ├── admin.py           # Админ-панель
│   ├── serializers.py     # DRF сериализаторы
│   └── urls.py            # URL-маршруты
├── ocr/                   # OCR модуль для чеков
│   ├── services.py        # OCR сервис
│   ├── views.py           # API для OCR
│   └── urls.py            # URL-маршруты OCR
├── analytics/             # Аналитика и отчеты
│   ├── views.py           # API для аналитики
│   └── urls.py            # URL-маршруты аналитики
├── integrations/          # Интеграции (1С, API)
│   ├── views.py           # API для интеграций
│   └── urls.py            # URL-маршруты интеграций
├── config/                # Конфигурация Django
│   ├── settings.py        # Настройки проекта
│   ├── urls.py            # Основные URL-маршруты
│   └── wsgi.py            # WSGI конфигурация
├── static/                # Статические файлы
├── media/                 # Загружаемые файлы
├── logs/                  # Логи приложения
├── requirements.txt       # Зависимости Python
├── manage.py              # Django management
├── run_bot.py             # Запуск Telegram бота
├── manage_finflow.py      # Управление проектом
├── env.example            # Пример переменных окружения
└── README.md              # Документация
```

## Быстрый старт

### 1. Клонирование и настройка

```bash
# Клонируйте репозиторий
git clone <repository-url>
cd FinFlow

# Создайте виртуальное окружение
python3 -m venv venv
source venv/bin/activate  # На Linux/Mac
# или
venv\Scripts\activate     # На Windows

# Установите зависимости
pip install -r requirements.txt
```

### 2. Настройка переменных окружения

```bash
# Скопируйте пример файла
cp env.example .env

# Отредактируйте .env файл
nano .env
```

Заполните следующие параметры:
```env
# Django
SECRET_KEY=your_secret_key_here
DEBUG=True

# База данных
DB_NAME=finflow
DB_USER=postgres
DB_PASSWORD=your_password

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token_here

# 1С Integration (опционально)
ONEC_BASE_URL=https://your-1c-server.com
ONEC_USERNAME=your_username
ONEC_PASSWORD=your_password
```

### 3. Настройка базы данных

```bash
# Создайте базу данных PostgreSQL
createdb finflow

# Примените миграции
python manage.py migrate

# Создайте суперпользователя
python manage.py createsuperuser
```

### 4. Запуск проекта

#### Вариант 1: Использование скрипта управления
```bash
python manage_finflow.py
```

#### Вариант 2: Ручной запуск

**Запуск Django сервера:**
```bash
python manage.py runserver
```
Сервер будет доступен по адресу: http://127.0.0.1:8000/

**Запуск Telegram бота:**
```bash
python run_bot.py
```

## Использование

### Telegram Bot

1. Найдите бота в Telegram по токену
2. Отправьте команду `/start`
3. Используйте команду `/receipt` для загрузки чека
4. Получайте аналитику командами `/summary`, `/report`, `/recommendations`

### Админ-панель

1. Откройте http://127.0.0.1:8000/admin/
2. Войдите с учетными данными суперпользователя
3. Управляйте данными через веб-интерфейс

### API

API доступно по адресу http://127.0.0.1:8000/api/

Основные endpoints:
- `/api/receipts/` - управление чеками
- `/api/categories/` - управление категориями
- `/api/analytics/summary/` - ежедневная сводка
- `/api/analytics/monthly/` - месячный отчет
- `/api/recommendations/` - финансовые рекомендации

## Разработка

### Структура кода

Проект следует принципам:
- **Модульность** - разделение на логические модули
- **Сервис-ориентированная архитектура** - бизнес-логика в сервисах
- **Dependency Injection** - внедрение зависимостей
- **Асинхронность** - использование async/await для I/O операций

### Добавление новых функций

1. **Модели**: Добавьте в `django_app/models.py`
2. **Сервисы**: Создайте в `core/services.py`
3. **API**: Добавьте views в соответствующие модули
4. **Бот**: Расширьте `bot/bot.py`

### Тестирование

```bash
# Запуск тестов
python manage.py test

# Проверка кода
python manage.py check
```

## Развертывание

### Продакшн

1. Установите `DEBUG=False` в `.env`
2. Настройте PostgreSQL для продакшна
3. Настройте Redis для очередей
4. Используйте Gunicorn + Nginx
5. Настройте SSL сертификаты

### Docker (планируется)

```bash
# Сборка и запуск
docker-compose up -d

# Остановка
docker-compose down
```

## Устранение неполадок

### Частые проблемы

1. **Ошибка подключения к базе данных**
   - Проверьте настройки PostgreSQL
   - Убедитесь, что сервер запущен

2. **Ошибка OCR**
   - Установите Tesseract: `brew install tesseract` (Mac)
   - Проверьте путь в `TESSERACT_CMD`

3. **Ошибка Telegram бота**
   - Проверьте токен в `.env`
   - Убедитесь, что бот не заблокирован

### Логи

Логи доступны в директории `logs/`:
- `finflow.log` - общие логи Django
- Логи бота выводятся в консоль

## Лицензия

MIT License

## Авторы

FinFlow Team

## Поддержка

- Создайте Issue в GitHub
- Обратитесь к документации
- Проверьте логи приложения

---

**FinFlow** - Умное управление финансами для вашего бизнеса! 🚀
