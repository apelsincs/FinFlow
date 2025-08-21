"""
FinFlow - Telegram Bot
Стратегия: Интуитивный интерфейс для загрузки чеков и получения финансовой аналитики
через удобные команды и inline-кнопки
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)

# Импорты из Django приложения
from django_app.models import Receipt, Business, Category, TelegramUser
from core.services import ReceiptService, AnalyticsService, RecommendationService
from ocr.services import OCRService


# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота
# TODO: Получить токен из настроек Django
bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN', 'your_bot_token_here'))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Состояния FSM для обработки чеков
class ReceiptStates(StatesGroup):
    """Состояния для обработки загрузки чека"""
    waiting_for_image = State()
    waiting_for_business = State()
    waiting_for_category = State()
    waiting_for_amount = State()
    waiting_for_date = State()


class ReceiptHandler:
    """Обработчик загрузки и обработки чеков"""
    
    def __init__(self):
        self.ocr_service = OCRService()
        self.receipt_service = ReceiptService()
    
    async def start_receipt_upload(self, message: types.Message, state: FSMContext):
        """Начало процесса загрузки чека"""
        await message.answer(
            "📸 Отправьте фотографию чека для анализа.\n\n"
            "Убедитесь, что чек хорошо освещен и текст читаем."
        )
        await state.set_state(ReceiptStates.waiting_for_image)
    
    async def process_receipt_image(self, message: types.Message, state: FSMContext):
        """Обработка загруженного изображения чека"""
        try:
            # Сохраняем изображение
            photo = message.photo[-1]
            file_info = await bot.get_file(photo.file_id)
            file_path = file_info.file_path
            
            # Скачиваем файл
            downloaded_file = await bot.download_file(file_path)
            
            # Сохраняем во временную директорию
            temp_path = f"/tmp/receipt_{message.from_user.id}_{datetime.now().timestamp()}.jpg"
            with open(temp_path, 'wb') as f:
                f.write(downloaded_file.read())
            
            # OCR распознавание
            await message.answer("🔍 Анализирую чек...")
            ocr_result = await self.ocr_service.process_receipt(temp_path)
            
            # Сохраняем результат в состояние
            await state.update_data(
                image_path=temp_path,
                ocr_text=ocr_result.get('text', ''),
                ocr_confidence=ocr_result.get('confidence', 0.0),
                extracted_data=ocr_result.get('extracted_data', {})
            )
            
            # Показываем результат распознавания
            extracted = ocr_result.get('extracted_data', {})
            response_text = "✅ Чек успешно распознан!\n\n"
            
            if extracted.get('total_amount'):
                response_text += f"💰 Сумма: {extracted['total_amount']} ₽\n"
            if extracted.get('seller_name'):
                response_text += f"🏪 Продавец: {extracted['seller_name']}\n"
            if extracted.get('receipt_date'):
                response_text += f"📅 Дата: {extracted['receipt_date']}\n"
            
            response_text += f"\n📊 Уверенность распознавания: {ocr_result.get('confidence', 0):.1%}"
            
            # Кнопки для подтверждения или корректировки
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_receipt"),
                    InlineKeyboardButton(text="✏️ Корректировать", callback_data="edit_receipt")
                ]
            ])
            
            await message.answer(response_text, reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Ошибка обработки изображения: {e}")
            await message.answer(
                "❌ Произошла ошибка при обработке изображения.\n"
                "Попробуйте еще раз или обратитесь в поддержку."
            )
            await state.clear()


class AnalyticsHandler:
    """Обработчик аналитических запросов"""
    
    def __init__(self):
        self.analytics_service = AnalyticsService()
    
    async def show_daily_summary(self, message: types.Message):
        """Показать ежедневную сводку расходов"""
        try:
            user_id = message.from_user.id
            summary = await self.analytics_service.get_daily_summary(user_id)
            
            response_text = "📊 Ежедневная сводка расходов\n\n"
            
            if summary['total_spent'] > 0:
                response_text += f"💰 Общие расходы: {summary['total_spent']} ₽\n"
                response_text += f"📈 Средний чек: {summary['average_receipt']} ₽\n"
                response_text += f"📝 Количество чеков: {summary['receipts_count']}\n\n"
                
                if summary['top_categories']:
                    response_text += "🏆 Топ категорий:\n"
                    for category, amount in summary['top_categories'][:3]:
                        response_text += f"• {category}: {amount} ₽\n"
            else:
                response_text += "🎉 Сегодня расходов нет!"
            
            await message.answer(response_text)
            
        except Exception as e:
            logger.error(f"Ошибка получения сводки: {e}")
            await message.answer("❌ Не удалось получить сводку. Попробуйте позже.")
    
    async def show_monthly_report(self, message: types.Message):
        """Показать месячный отчет"""
        try:
            user_id = message.from_user.id
            report = await self.analytics_service.get_monthly_report(user_id)
            
            response_text = "📈 Месячный отчет\n\n"
            response_text += f"💰 Общие расходы: {report['total_spent']} ₽\n"
            response_text += f"📊 Среднедневные расходы: {report['daily_average']} ₽\n"
            response_text += f"📝 Всего чеков: {report['total_receipts']}\n\n"
            
            if report['category_breakdown']:
                response_text += "📋 По категориям:\n"
                for category, data in report['category_breakdown'].items():
                    percentage = (data['amount'] / report['total_spent']) * 100
                    response_text += f"• {category}: {data['amount']} ₽ ({percentage:.1f}%)\n"
            
            await message.answer(response_text)
            
        except Exception as e:
            logger.error(f"Ошибка получения отчета: {e}")
            await message.answer("❌ Не удалось получить отчет. Попробуйте позже.")


class RecommendationHandler:
    """Обработчик рекомендаций по оптимизации"""
    
    def __init__(self):
        self.recommendation_service = RecommendationService()
    
    async def show_recommendations(self, message: types.Message):
        """Показать финансовые рекомендации"""
        try:
            user_id = message.from_user.id
            recommendations = await self.recommendation_service.get_user_recommendations(user_id)
            
            if not recommendations:
                await message.answer("🎯 У вас пока нет рекомендаций. Продолжайте загружать чеки!")
                return
            
            response_text = "💡 Финансовые рекомендации\n\n"
            
            for i, rec in enumerate(recommendations[:5], 1):
                priority_emoji = {
                    'low': '🟢',
                    'medium': '🟡', 
                    'high': '🟠',
                    'critical': '🔴'
                }
                
                response_text += f"{i}. {priority_emoji.get(rec.priority, '⚪')} {rec.title}\n"
                response_text += f"   {rec.description[:100]}...\n\n"
            
            if len(recommendations) > 5:
                response_text += f"📋 И еще {len(recommendations) - 5} рекомендаций..."
            
            await message.answer(response_text)
            
        except Exception as e:
            logger.error(f"Ошибка получения рекомендаций: {e}")
            await message.answer("❌ Не удалось получить рекомендации. Попробуйте позже.")


# Инициализация обработчиков
receipt_handler = ReceiptHandler()
analytics_handler = AnalyticsHandler()
recommendation_handler = RecommendationHandler()


# Команды бота
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    """Обработка команды /start"""
    welcome_text = (
        "🎉 Добро пожаловать в FinFlow!\n\n"
        "Я помогу вам анализировать расходы и оптимизировать бюджет.\n\n"
        "📱 Основные команды:\n"
        "/receipt - Загрузить чек\n"
        "/summary - Ежедневная сводка\n"
        "/report - Месячный отчет\n"
        "/recommendations - Рекомендации\n"
        "/help - Справка\n\n"
        "Начните с загрузки чека командой /receipt"
    )
    
    # Главное меню
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📸 Загрузить чек"), KeyboardButton(text="📊 Сводка")],
            [KeyboardButton(text="📈 Отчет"), KeyboardButton(text="💡 Рекомендации")],
            [KeyboardButton(text="⚙️ Настройки"), KeyboardButton(text="❓ Помощь")]
        ],
        resize_keyboard=True
    )
    
    await message.answer(welcome_text, reply_markup=keyboard)


@dp.message(Command("receipt"))
async def cmd_receipt(message: types.Message, state: FSMContext):
    """Обработка команды загрузки чека"""
    await receipt_handler.start_receipt_upload(message, state)


@dp.message(Command("summary"))
async def cmd_summary(message: types.Message):
    """Обработка команды ежедневной сводки"""
    await analytics_handler.show_daily_summary(message)


@dp.message(Command("report"))
async def cmd_report(message: types.Message):
    """Обработка команды месячного отчета"""
    await analytics_handler.show_monthly_report(message)


@dp.message(Command("recommendations"))
async def cmd_recommendations(message: types.Message):
    """Обработка команды рекомендаций"""
    await recommendation_handler.show_recommendations(message)


@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """Обработка команды помощи"""
    help_text = (
        "❓ Справка по командам FinFlow\n\n"
        "📸 /receipt - Загрузить чек для анализа\n"
        "📊 /summary - Ежедневная сводка расходов\n"
        "📈 /report - Месячный отчет по категориям\n"
        "💡 /recommendations - Персональные рекомендации\n"
        "⚙️ /settings - Настройки уведомлений\n"
        "❓ /help - Эта справка\n\n"
        "💡 Совет: Используйте кнопки меню для быстрого доступа к функциям!"
    )
    await message.answer(help_text)


# Обработка текстовых сообщений
@dp.message(F.text == "📸 Загрузить чек")
async def handle_receipt_button(message: types.Message, state: FSMContext):
    """Обработка нажатия кнопки загрузки чека"""
    await receipt_handler.start_receipt_upload(message, state)


@dp.message(F.text == "📊 Сводка")
async def handle_summary_button(message: types.Message):
    """Обработка нажатия кнопки сводки"""
    await analytics_handler.show_daily_summary(message)


@dp.message(F.text == "📈 Отчет")
async def handle_report_button(message: types.Message):
    """Обработка нажатия кнопки отчета"""
    await analytics_handler.show_monthly_report(message)


@dp.message(F.text == "💡 Рекомендации")
async def handle_recommendations_button(message: types.Message):
    """Обработка нажатия кнопки рекомендаций"""
    await recommendation_handler.show_recommendations(message)


# Обработка изображений
@dp.message(ReceiptStates.waiting_for_image, F.photo)
async def handle_receipt_photo(message: types.Message, state: FSMContext):
    """Обработка загруженного изображения чека"""
    await receipt_handler.process_receipt_image(message, state)


# Обработка callback-запросов
@dp.callback_query(F.data == "confirm_receipt")
async def confirm_receipt(callback: types.CallbackQuery, state: FSMContext):
    """Подтверждение распознанного чека"""
    try:
        data = await state.get_data()
        
        # Создаем чек в базе данных
        receipt = await receipt_handler.receipt_service.create_receipt_from_ocr(
            user_id=callback.from_user.id,
            ocr_data=data
        )
        
        await callback.message.edit_text(
            f"✅ Чек успешно сохранен!\n\n"
            f"📝 Номер: {receipt.receipt_number or 'Не указан'}\n"
            f"💰 Сумма: {receipt.total_amount} ₽\n"
            f"🏪 Продавец: {receipt.seller_name or 'Не указан'}\n\n"
            f"Чек будет проанализирован и добавлен в вашу статистику."
        )
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Ошибка сохранения чека: {e}")
        await callback.message.edit_text(
            "❌ Произошла ошибка при сохранении чека.\n"
            "Попробуйте еще раз или обратитесь в поддержку."
        )
        await state.clear()


@dp.callback_query(F.data == "edit_receipt")
async def edit_receipt(callback: types.CallbackQuery, state: FSMContext):
    """Редактирование распознанного чека"""
    await callback.message.edit_text(
        "✏️ Редактирование чека\n\n"
        "Функция редактирования находится в разработке.\n"
        "Пока что чек будет сохранен с автоматически распознанными данными."
    )
    
    # TODO: Реализовать редактирование чека
    await state.clear()


# Обработка ошибок
@dp.errors()
async def errors_handler(update: types.Update, exception: Exception):
    """Обработчик ошибок"""
    logger.error(f"Ошибка в боте: {exception}")
    
    if update.message:
        await update.message.answer(
            "❌ Произошла ошибка. Попробуйте еще раз или обратитесь в поддержку."
        )


async def main():
    """Главная функция запуска бота"""
    logger.info("Запуск FinFlow Telegram Bot...")
    
    try:
        # Запуск бота
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
