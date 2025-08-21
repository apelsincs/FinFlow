"""
FinFlow - Админ-панель Django
Стратегия: Удобное управление всеми финансовыми данными через веб-интерфейс
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Business, Category, Receipt, ReceiptItem, 
    Budget, FinancialRecommendation, TelegramUser
)


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    """Администрирование бизнесов"""
    list_display = ['name', 'owner', 'onec_enabled', 'created_at', 'updated_at']
    list_filter = ['onec_enabled', 'created_at']
    search_fields = ['name', 'owner__username', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'owner', 'description')
        }),
        ('Интеграция с 1С', {
            'fields': ('onec_enabled', 'onec_company_id'),
            'classes': ('collapse',)
        }),
        ('Метаданные', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Администрирование категорий расходов"""
    list_display = ['name', 'business', 'parent', 'color_display', 'keywords_count']
    list_filter = ['business', 'parent']
    search_fields = ['name', 'business__name']
    
    def color_display(self, obj):
        """Отображение цвета категории"""
        if obj.color:
            return format_html(
                '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px;">{}</span>',
                obj.color, obj.color
            )
        return '-'
    color_display.short_description = 'Цвет'
    
    def keywords_count(self, obj):
        """Количество ключевых слов"""
        return len(obj.keywords) if obj.keywords else 0
    keywords_count.short_description = 'Ключевых слов'


@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    """Администрирование чеков"""
    list_display = [
        'receipt_number', 'business', 'user', 'total_amount', 
        'seller_name', 'status', 'receipt_date', 'onec_synced'
    ]
    list_filter = ['status', 'onec_synced', 'receipt_date', 'business']
    search_fields = ['receipt_number', 'seller_name', 'user__username']
    readonly_fields = ['created_at', 'updated_at', 'ocr_text', 'ocr_confidence']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('business', 'user', 'receipt_number', 'receipt_date', 'total_amount')
        }),
        ('Продавец', {
            'fields': ('seller_name', 'seller_inn', 'seller_address')
        }),
        ('Статус и обработка', {
            'fields': ('status', 'image')
        }),
        ('OCR данные', {
            'fields': ('ocr_text', 'ocr_confidence'),
            'classes': ('collapse',)
        }),
        ('Интеграция с 1С', {
            'fields': ('onec_document_id', 'onec_synced'),
            'classes': ('collapse',)
        }),
        ('Метаданные', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Оптимизация запросов"""
        return super().get_queryset(request).select_related('business', 'user')


@admin.register(ReceiptItem)
class ReceiptItemAdmin(admin.ModelAdmin):
    """Администрирование позиций в чеках"""
    list_display = ['name', 'receipt', 'quantity', 'price', 'total', 'category', 'category_confidence']
    list_filter = ['category', 'receipt__business']
    search_fields = ['name', 'receipt__receipt_number']
    
    def get_queryset(self, request):
        """Оптимизация запросов"""
        return super().get_queryset(request).select_related('receipt', 'category')


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    """Администрирование бюджетов"""
    list_display = ['business', 'category', 'period', 'amount', 'start_date', 'end_date', 'notify_at_80', 'notify_at_100']
    list_filter = ['period', 'notify_at_80', 'notify_at_100', 'start_date']
    search_fields = ['business__name', 'category__name']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('business', 'category', 'period', 'amount')
        }),
        ('Период', {
            'fields': ('start_date', 'end_date')
        }),
        ('Уведомления', {
            'fields': ('notify_at_80', 'notify_at_100')
        }),
    )


@admin.register(FinancialRecommendation)
class FinancialRecommendationAdmin(admin.ModelAdmin):
    """Администрирование финансовых рекомендаций"""
    list_display = [
        'title', 'business', 'recommendation_type', 'priority', 
        'status', 'estimated_savings', 'created_at'
    ]
    list_filter = ['recommendation_type', 'priority', 'status', 'created_at']
    search_fields = ['title', 'description', 'business__name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'description', 'business', 'recommendation_type')
        }),
        ('Приоритет и статус', {
            'fields': ('priority', 'status')
        }),
        ('Связанные данные', {
            'fields': ('related_categories', 'estimated_savings')
        }),
        ('Метаданные', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    filter_horizontal = ['related_categories']


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    """Администрирование пользователей Telegram"""
    list_display = [
        'user', 'telegram_id', 'username', 'first_name', 'last_name',
        'notifications_enabled', 'total_receipts', 'last_activity'
    ]
    list_filter = ['notifications_enabled', 'daily_summary', 'budget_alerts', 'last_activity']
    search_fields = ['user__username', 'username', 'first_name', 'last_name']
    readonly_fields = ['last_activity', 'total_receipts']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'telegram_id', 'username', 'first_name', 'last_name')
        }),
        ('Настройки уведомлений', {
            'fields': ('notifications_enabled', 'daily_summary', 'budget_alerts')
        }),
        ('Статистика', {
            'fields': ('total_receipts', 'last_activity'),
            'classes': ('collapse',)
        }),
    )


# Настройка админ-сайта
admin.site.site_header = "FinFlow - Администрирование"
admin.site.site_title = "FinFlow Admin"
admin.site.index_title = "Добро пожаловать в FinFlow"
