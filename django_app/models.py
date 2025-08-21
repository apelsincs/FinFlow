"""
FinFlow - Основные модели Django приложения
Стратегия: Централизованное хранение всех финансовых данных с возможностью
интеграции с внешними системами (1С, банки, кассы)
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal


class Business(models.Model):
    """
    Модель бизнеса - основная сущность для группировки всех финансовых операций
    Стратегия: Один пользователь может управлять несколькими бизнесами
    """
    name = models.CharField(max_length=200, verbose_name="Название бизнеса")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Владелец")
    description = models.TextField(blank=True, verbose_name="Описание")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    
    # Настройки интеграции
    onec_enabled = models.BooleanField(default=False, verbose_name="Интеграция с 1С")
    onec_company_id = models.CharField(max_length=100, blank=True, verbose_name="ID компании в 1С")
    
    class Meta:
        verbose_name = "Бизнес"
        verbose_name_plural = "Бизнесы"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class Category(models.Model):
    """
    Категории расходов для группировки и анализа
    Стратегия: Иерархическая структура категорий с возможностью
    автоматического определения по ключевым словам
    """
    name = models.CharField(max_length=100, verbose_name="Название категории")
    business = models.ForeignKey(Business, on_delete=models.CASCADE, verbose_name="Бизнес")
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, verbose_name="Родительская категория")
    color = models.CharField(max_length=7, default="#007bff", verbose_name="Цвет категории")
    
    # Ключевые слова для автоматического определения категории
    keywords = models.JSONField(default=list, verbose_name="Ключевые слова")
    
    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        unique_together = ['name', 'business']
    
    def __str__(self):
        return self.name


class Receipt(models.Model):
    """
    Модель чека - основная сущность для хранения данных о покупках
    Стратегия: OCR распознавание + ручная корректировка + интеграция с 1С
    """
    business = models.ForeignKey(Business, on_delete=models.CASCADE, verbose_name="Бизнес")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    
    # Данные чека
    receipt_number = models.CharField(max_length=100, blank=True, verbose_name="Номер чека")
    receipt_date = models.DateTimeField(verbose_name="Дата и время чека")
    total_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Общая сумма"
    )
    
    # Информация о продавце
    seller_name = models.CharField(max_length=200, blank=True, verbose_name="Название продавца")
    seller_inn = models.CharField(max_length=12, blank=True, verbose_name="ИНН продавца")
    seller_address = models.TextField(blank=True, verbose_name="Адрес продавца")
    
    # Статус обработки
    STATUS_CHOICES = [
        ('pending', 'Ожидает обработки'),
        ('processing', 'Обрабатывается'),
        ('completed', 'Обработан'),
        ('error', 'Ошибка обработки'),
        ('manual', 'Требует ручной корректировки'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Статус")
    
    # OCR данные
    ocr_text = models.TextField(blank=True, verbose_name="Распознанный текст")
    ocr_confidence = models.FloatField(null=True, blank=True, verbose_name="Уверенность OCR")
    
    # Изображение чека
    image = models.ImageField(upload_to='receipts/', verbose_name="Изображение чека")
    
    # Метаданные
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    
    # Интеграция с 1С
    onec_document_id = models.CharField(max_length=100, blank=True, verbose_name="ID документа в 1С")
    onec_synced = models.BooleanField(default=False, verbose_name="Синхронизировано с 1С")
    
    class Meta:
        verbose_name = "Чек"
        verbose_name_plural = "Чеки"
        ordering = ['-receipt_date']
    
    def __str__(self):
        return f"Чек {self.receipt_number} от {self.receipt_date.strftime('%d.%m.%Y')}"


class ReceiptItem(models.Model):
    """
    Позиции в чеке - детализация покупок
    Стратегия: Автоматическое определение категории по названию товара
    """
    receipt = models.ForeignKey(Receipt, on_delete=models.CASCADE, verbose_name="Чек")
    name = models.CharField(max_length=200, verbose_name="Название товара/услуги")
    quantity = models.DecimalField(max_digits=8, decimal_places=3, verbose_name="Количество")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена за единицу")
    total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Общая стоимость")
    
    # Автоматически определенная категория
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="Категория")
    category_confidence = models.FloatField(null=True, blank=True, verbose_name="Уверенность определения категории")
    
    class Meta:
        verbose_name = "Позиция в чеке"
        verbose_name_plural = "Позиции в чеке"
    
    def __str__(self):
        return f"{self.name} - {self.quantity} x {self.price}"


class Budget(models.Model):
    """
    Бюджетные ограничения по категориям
    Стратегия: Контроль расходов с уведомлениями о превышении лимитов
    """
    business = models.ForeignKey(Business, on_delete=models.CASCADE, verbose_name="Бизнес")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Категория")
    period = models.CharField(max_length=20, choices=[
        ('monthly', 'Ежемесячно'),
        ('quarterly', 'Ежеквартально'),
        ('yearly', 'Ежегодно'),
    ], verbose_name="Период")
    
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Лимит бюджета")
    start_date = models.DateField(verbose_name="Дата начала периода")
    end_date = models.DateField(verbose_name="Дата окончания периода")
    
    # Уведомления
    notify_at_80 = models.BooleanField(default=True, verbose_name="Уведомлять при 80% расхода")
    notify_at_100 = models.BooleanField(default=True, verbose_name="Уведомлять при превышении")
    
    class Meta:
        verbose_name = "Бюджет"
        verbose_name_plural = "Бюджеты"
        unique_together = ['business', 'category', 'period', 'start_date']
    
    def __str__(self):
        return f"{self.category.name} - {self.period} ({self.start_date} - {self.end_date})"


class FinancialRecommendation(models.Model):
    """
    Рекомендации по оптимизации финансов
    Стратегия: AI-анализ расходов с конкретными советами по экономии
    """
    business = models.ForeignKey(Business, on_delete=models.CASCADE, verbose_name="Бизнес")
    title = models.CharField(max_length=200, verbose_name="Заголовок рекомендации")
    description = models.TextField(verbose_name="Описание рекомендации")
    
    # Тип рекомендации
    TYPE_CHOICES = [
        ('cost_reduction', 'Сокращение расходов'),
        ('category_optimization', 'Оптимизация категорий'),
        ('budget_planning', 'Планирование бюджета'),
        ('vendor_analysis', 'Анализ поставщиков'),
        ('seasonal_analysis', 'Сезонный анализ'),
    ]
    recommendation_type = models.CharField(max_length=30, choices=TYPE_CHOICES, verbose_name="Тип рекомендации")
    
    # Приоритет и статус
    priority = models.CharField(max_length=20, choices=[
        ('low', 'Низкий'),
        ('medium', 'Средний'),
        ('high', 'Высокий'),
        ('critical', 'Критический'),
    ], verbose_name="Приоритет")
    
    status = models.CharField(max_length=20, choices=[
        ('new', 'Новая'),
        ('in_progress', 'В работе'),
        ('completed', 'Выполнена'),
        ('ignored', 'Игнорируется'),
    ], default='new', verbose_name="Статус")
    
    # Метаданные
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    
    # Связанные данные
    related_categories = models.ManyToManyField(Category, blank=True, verbose_name="Связанные категории")
    estimated_savings = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        verbose_name="Ожидаемая экономия"
    )
    
    class Meta:
        verbose_name = "Финансовая рекомендация"
        verbose_name_plural = "Финансовые рекомендации"
        ordering = ['-priority', '-created_at']
    
    def __str__(self):
        return self.title


class TelegramUser(models.Model):
    """
    Расширенная модель пользователя Telegram
    Стратегия: Связь Telegram аккаунта с пользователем Django
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Пользователь Django")
    telegram_id = models.BigIntegerField(unique=True, verbose_name="Telegram ID")
    username = models.CharField(max_length=100, blank=True, verbose_name="Telegram username")
    first_name = models.CharField(max_length=100, blank=True, verbose_name="Имя")
    last_name = models.CharField(max_length=100, blank=True, verbose_name="Фамилия")
    
    # Настройки уведомлений
    notifications_enabled = models.BooleanField(default=True, verbose_name="Уведомления включены")
    daily_summary = models.BooleanField(default=True, verbose_name="Ежедневная сводка")
    budget_alerts = models.BooleanField(default=True, verbose_name="Уведомления о бюджете")
    
    # Статистика использования
    last_activity = models.DateTimeField(auto_now=True, verbose_name="Последняя активность")
    total_receipts = models.PositiveIntegerField(default=0, verbose_name="Всего чеков")
    
    class Meta:
        verbose_name = "Пользователь Telegram"
        verbose_name_plural = "Пользователи Telegram"
    
    def __str__(self):
        return f"{self.user.username} (@{self.username})"
