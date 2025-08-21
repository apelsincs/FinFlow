"""
FinFlow - Основные сервисы для работы с данными
Стратегия: Разделение бизнес-логики на отдельные сервисы для обеспечения
модульности, тестируемости и переиспользования кода
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal

from django.db.models import Sum, Count, Avg, Q
from django.contrib.auth.models import User
from django.utils import timezone

# Импортируем модели из django_app
from django_app.models import (
    Receipt, ReceiptItem, Business, Category, 
    Budget, FinancialRecommendation, TelegramUser
)

logger = logging.getLogger(__name__)


class ReceiptService:
    """Сервис для работы с чеками"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def create_receipt_from_ocr(
        self, 
        user_id: int, 
        ocr_data: Dict[str, Any]
    ) -> Receipt:
        """
        Создание чека на основе данных OCR
        Стратегия: Автоматическое создание с возможностью ручной корректировки
        """
        try:
            # Получаем пользователя
            user = await self._get_user_by_telegram_id(user_id)
            if not user:
                raise ValueError(f"Пользователь с Telegram ID {user_id} не найден")
            
            # Получаем бизнес пользователя (пока берем первый)
            business = await self._get_user_business(user)
            
            # Извлекаем данные из OCR
            extracted = ocr_data.get('extracted_data', {})
            
            # Создаем чек
            receipt = Receipt.objects.create(
                business=business,
                user=user,
                receipt_number=extracted.get('receipt_number', ''),
                receipt_date=extracted.get('receipt_date') or timezone.now(),
                total_amount=extracted.get('total_amount') or Decimal('0.00'),
                seller_name=extracted.get('seller_name', ''),
                seller_inn=extracted.get('seller_inn', ''),
                seller_address='',
                status='completed',
                ocr_text=ocr_data.get('text', ''),
                ocr_confidence=ocr_data.get('confidence', 0.0),
                image='',  # TODO: Сохранить изображение
            )
            
            # Создаем позиции товаров если есть
            if 'items' in ocr_data:
                await self._create_receipt_items(receipt, ocr_data['items'])
            
            # Обновляем статистику пользователя
            await self._update_user_statistics(user_id)
            
            self.logger.info(f"Чек {receipt.id} успешно создан для пользователя {user.username}")
            return receipt
            
        except Exception as e:
            self.logger.error(f"Ошибка создания чека: {e}")
            raise
    
    async def _get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Получение пользователя Django по Telegram ID"""
        try:
            telegram_user = TelegramUser.objects.get(telegram_id=telegram_id)
            return telegram_user.user
        except TelegramUser.DoesNotExist:
            return None
    
    async def _get_user_business(self, user: User) -> Business:
        """Получение бизнеса пользователя"""
        try:
            return Business.objects.filter(owner=user).first()
        except Business.DoesNotExist:
            # Создаем бизнес по умолчанию
            return Business.objects.create(
                name=f"Бизнес {user.username}",
                owner=user,
                description="Автоматически созданный бизнес"
            )
    
    async def _create_receipt_items(
        self, 
        receipt: Receipt, 
        items_data: List[Dict[str, Any]]
    ) -> None:
        """Создание позиций товаров в чеке"""
        for item_data in items_data:
            try:
                # Определяем категорию по названию товара
                category = await self._determine_item_category(
                    item_data['name'], 
                    receipt.business
                )
                
                ReceiptItem.objects.create(
                    receipt=receipt,
                    name=item_data['name'],
                    quantity=item_data['quantity'],
                    price=item_data['unit_price'],
                    total=item_data['total_price'],
                    category=category,
                    category_confidence=0.8 if category else None,
                )
            except Exception as e:
                self.logger.error(f"Ошибка создания позиции товара: {e}")
    
    async def _determine_item_category(
        self, 
        item_name: str, 
        business: Business
    ) -> Optional[Category]:
        """Автоматическое определение категории товара по названию"""
        try:
            # Ищем категорию по ключевым словам
            categories = Category.objects.filter(business=business)
            
            for category in categories:
                if category.keywords:
                    for keyword in category.keywords:
                        if keyword.lower() in item_name.lower():
                            return category
            
            return None
            
        except Exception as e:
            self.logger.error(f"Ошибка определения категории: {e}")
            return None
    
    async def _update_user_statistics(self, telegram_id: int) -> None:
        """Обновление статистики пользователя"""
        try:
            telegram_user = TelegramUser.objects.get(telegram_id=telegram_id)
            telegram_user.total_receipts = Receipt.objects.filter(
                user=telegram_user.user
            ).count()
            telegram_user.save()
        except Exception as e:
            self.logger.error(f"Ошибка обновления статистики: {e}")


class AnalyticsService:
    """Сервис для аналитики и отчетов"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def get_daily_summary(self, user_id: int) -> Dict[str, Any]:
        """
        Получение ежедневной сводки расходов
        Стратегия: Агрегация данных по дням с группировкой по категориям
        """
        try:
            user = await self._get_user_by_telegram_id(user_id)
            if not user:
                return self._empty_summary()
            
            today = timezone.now().date()
            
            # Получаем чеки за сегодня
            today_receipts = Receipt.objects.filter(
                user=user,
                receipt_date__date=today,
                status='completed'
            )
            
            if not today_receipts.exists():
                return self._empty_summary()
            
            # Общие расходы
            total_spent = today_receipts.aggregate(
                total=Sum('total_amount')
            )['total'] or Decimal('0.00')
            
            # Средний чек
            average_receipt = today_receipts.aggregate(
                avg=Avg('total_amount')
            )['avg'] or Decimal('0.00')
            
            # Количество чеков
            receipts_count = today_receipts.count()
            
            # Топ категорий
            top_categories = await self._get_top_categories(today_receipts)
            
            return {
                'total_spent': total_spent,
                'average_receipt': average_receipt,
                'receipts_count': receipts_count,
                'top_categories': top_categories,
                'date': today.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка получения ежедневной сводки: {e}")
            return self._empty_summary()
    
    async def get_monthly_report(self, user_id: int) -> Dict[str, Any]:
        """
        Получение месячного отчета
        Стратегия: Детальная аналитика по месяцам с разбивкой по категориям
        """
        try:
            user = await self._get_user_by_telegram_id(user_id)
            if not user:
                return self._empty_report()
            
            # Определяем текущий месяц
            now = timezone.now()
            start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
            
            # Получаем чеки за месяц
            monthly_receipts = Receipt.objects.filter(
                user=user,
                receipt_date__range=(start_of_month, end_of_month),
                status='completed'
            )
            
            if not monthly_receipts.exists():
                return self._empty_report()
            
            # Общие расходы
            total_spent = monthly_receipts.aggregate(
                total=Sum('total_amount')
            )['total'] or Decimal('0.00')
            
            # Среднедневные расходы
            days_in_month = (end_of_month - start_of_month).days + 1
            daily_average = total_spent / days_in_month
            
            # Общее количество чеков
            total_receipts = monthly_receipts.count()
            
            # Разбивка по категориям
            category_breakdown = await self._get_category_breakdown(monthly_receipts)
            
            return {
                'total_spent': total_spent,
                'daily_average': daily_average,
                'total_receipts': total_receipts,
                'category_breakdown': category_breakdown,
                'period': {
                    'start': start_of_month.isoformat(),
                    'end': end_of_month.isoformat()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка получения месячного отчета: {e}")
            return self._empty_report()
    
    async def _get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Получение пользователя Django по Telegram ID"""
        try:
            telegram_user = TelegramUser.objects.get(telegram_id=telegram_id)
            return telegram_user.user
        except TelegramUser.DoesNotExist:
            return None
    
    async def _get_top_categories(self, receipts) -> List[tuple]:
        """Получение топ категорий по расходам"""
        try:
            # Группируем по категориям через позиции товаров
            category_totals = {}
            
            for receipt in receipts:
                items = ReceiptItem.objects.filter(receipt=receipt)
                for item in items:
                    if item.category:
                        category_name = item.category.name
                        if category_name not in category_totals:
                            category_totals[category_name] = Decimal('0.00')
                        category_totals[category_name] += item.total
            
            # Сортируем по убыванию
            sorted_categories = sorted(
                category_totals.items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            
            return sorted_categories[:5]  # Топ 5
            
        except Exception as e:
            self.logger.error(f"Ошибка получения топ категорий: {e}")
            return []
    
    async def _get_category_breakdown(self, receipts) -> Dict[str, Dict[str, Any]]:
        """Получение детальной разбивки по категориям"""
        try:
            category_data = {}
            
            for receipt in receipts:
                items = ReceiptItem.objects.filter(receipt=receipt)
                for item in items:
                    if item.category:
                        category_name = item.category.name
                        if category_name not in category_data:
                            category_data[category_name] = {
                                'amount': Decimal('0.00'),
                                'count': 0,
                                'avg_price': Decimal('0.00')
                            }
                        
                        category_data[category_name]['amount'] += item.total
                        category_data[category_name]['count'] += 1
            
            # Вычисляем средние цены
            for category_name, data in category_data.items():
                if data['count'] > 0:
                    data['avg_price'] = data['amount'] / data['count']
            
            return category_data
            
        except Exception as e:
            self.logger.error(f"Ошибка получения разбивки по категориям: {e}")
            return {}
    
    def _empty_summary(self) -> Dict[str, Any]:
        """Пустая сводка"""
        return {
            'total_spent': Decimal('0.00'),
            'average_receipt': Decimal('0.00'),
            'receipts_count': 0,
            'top_categories': [],
            'date': timezone.now().date().isoformat()
        }
    
    def _empty_report(self) -> Dict[str, Any]:
        """Пустой отчет"""
        return {
            'total_spent': Decimal('0.00'),
            'daily_average': Decimal('0.00'),
            'total_receipts': 0,
            'category_breakdown': {},
            'period': {
                'start': timezone.now().replace(day=1).isoformat(),
                'end': timezone.now().isoformat()
            }
        }


class RecommendationService:
    """Сервис для генерации финансовых рекомендаций"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def get_user_recommendations(self, telegram_id: int) -> List[FinancialRecommendation]:
        """
        Получение персональных рекомендаций для пользователя
        Стратегия: Анализ паттернов расходов и генерация конкретных советов
        """
        try:
            user = await self._get_user_by_telegram_id(telegram_id)
            if not user:
                return []
            
            # Получаем существующие рекомендации
            existing_recommendations = FinancialRecommendation.objects.filter(
                business__owner=user,
                status__in=['new', 'in_progress']
            ).order_by('-priority', '-created_at')
            
            if existing_recommendations.exists():
                return list(existing_recommendations)
            
            # Генерируем новые рекомендации если их нет
            await self._generate_recommendations(user)
            
            # Возвращаем сгенерированные рекомендации
            return list(FinancialRecommendation.objects.filter(
                business__owner=user,
                status='new'
            ).order_by('-priority', '-created_at'))
            
        except Exception as e:
            self.logger.error(f"Ошибка получения рекомендаций: {e}")
            return []
    
    async def _generate_recommendations(self, user: User) -> None:
        """Генерация новых рекомендаций на основе анализа расходов"""
        try:
            business = await self._get_user_business(user)
            
            # Анализируем расходы за последние 30 дней
            thirty_days_ago = timezone.now() - timedelta(days=30)
            recent_receipts = Receipt.objects.filter(
                business=business,
                receipt_date__gte=thirty_days_ago,
                status='completed'
            )
            
            if not recent_receipts.exists():
                return
            
            # Анализируем паттерны и генерируем рекомендации
            await self._analyze_spending_patterns(recent_receipts, business)
            
        except Exception as e:
            self.logger.error(f"Ошибка генерации рекомендаций: {e}")
    
    async def _analyze_spending_patterns(
        self, 
        receipts, 
        business: Business
    ) -> None:
        """Анализ паттернов расходов и генерация рекомендаций"""
        try:
            # Анализ по категориям
            category_totals = {}
            for receipt in receipts:
                items = ReceiptItem.objects.filter(receipt=receipt)
                for item in items:
                    if item.category:
                        category_name = item.category.name
                        if category_name not in category_totals:
                            category_totals[category_name] = {
                                'amount': Decimal('0.00'),
                                'count': 0
                            }
                        category_totals[category_name]['amount'] += item.total
                        category_totals[category_name]['count'] += 1
            
            # Генерируем рекомендации на основе анализа
            for category_name, data in category_totals.items():
                if data['amount'] > 10000:  # Если расходы по категории > 10k
                    await self._create_cost_reduction_recommendation(
                        business, category_name, data
                    )
                
                if data['count'] > 20:  # Если много мелких покупок
                    await self._create_optimization_recommendation(
                        business, category_name, data
                    )
            
            # Общие рекомендации по планированию бюджета
            total_spent = sum(data['amount'] for data in category_totals.values())
            if total_spent > 50000:  # Если общие расходы > 50k
                await self._create_budget_planning_recommendation(business, total_spent)
                
        except Exception as e:
            self.logger.error(f"Ошибка анализа паттернов: {e}")
    
    async def _create_cost_reduction_recommendation(
        self, 
        business: Business, 
        category_name: str, 
        data: Dict[str, Any]
    ) -> None:
        """Создание рекомендации по сокращению расходов"""
        try:
            title = f"Сокращение расходов по категории '{category_name}'"
            description = (
                f"За последний месяц расходы по категории '{category_name}' составили "
                f"{data['amount']} ₽ ({data['count']} покупок). "
                f"Рекомендуем проанализировать необходимость каждой покупки "
                f"и рассмотреть альтернативные поставщики."
            )
            
            FinancialRecommendation.objects.create(
                business=business,
                title=title,
                description=description,
                recommendation_type='cost_reduction',
                priority='high',
                estimated_savings=data['amount'] * Decimal('0.15')  # Ожидаем 15% экономии
            )
            
        except Exception as e:
            self.logger.error(f"Ошибка создания рекомендации: {e}")
    
    async def _create_optimization_recommendation(
        self, 
        business: Business, 
        category_name: str, 
        data: Dict[str, Any]
    ) -> None:
        """Создание рекомендации по оптимизации покупок"""
        try:
            title = f"Оптимизация покупок в категории '{category_name}'"
            description = (
                f"В категории '{category_name}' зафиксировано {data['count']} покупок "
                f"на общую сумму {data['amount']} ₽. "
                f"Рекомендуем объединить мелкие покупки в более крупные заказы "
                f"для получения скидок от поставщиков."
            )
            
            FinancialRecommendation.objects.create(
                business=business,
                title=title,
                description=description,
                recommendation_type='category_optimization',
                priority='medium',
                estimated_savings=data['amount'] * Decimal('0.10')  # Ожидаем 10% экономии
            )
            
        except Exception as e:
            self.logger.error(f"Ошибка создания рекомендации: {e}")
    
    async def _create_budget_planning_recommendation(
        self, 
        business: Business, 
        total_spent: Decimal
    ) -> None:
        """Создание рекомендации по планированию бюджета"""
        try:
            title = "Планирование месячного бюджета"
            description = (
                f"Общие расходы за месяц составили {total_spent} ₽. "
                f"Рекомендуем установить месячные лимиты по категориям "
                f"и отслеживать их выполнение для контроля расходов."
            )
            
            FinancialRecommendation.objects.create(
                business=business,
                title=title,
                description=description,
                recommendation_type='budget_planning',
                priority='medium'
            )
            
        except Exception as e:
            self.logger.error(f"Ошибка создания рекомендации: {e}")
    
    async def _get_user_business(self, user: User) -> Business:
        """Получение бизнеса пользователя"""
        try:
            return Business.objects.filter(owner=user).first()
        except Business.DoesNotExist:
            return Business.objects.create(
                name=f"Бизнес {user.username}",
                owner=user,
                description="Автоматически созданный бизнес"
            )
    
    async def _get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Получение пользователя Django по Telegram ID"""
        try:
            telegram_user = TelegramUser.objects.get(telegram_id=telegram_id)
            return telegram_user.user
        except TelegramUser.DoesNotExist:
            return None
