"""
FinFlow - Сериализаторы для Django REST Framework
"""

from rest_framework import serializers
from .models import (
    Receipt, ReceiptItem, Category, Business, 
    Budget, FinancialRecommendation, TelegramUser
)


class BusinessSerializer(serializers.ModelSerializer):
    """Сериализатор для бизнеса"""
    
    class Meta:
        model = Business
        fields = ['id', 'name', 'description', 'onec_enabled', 'onec_company_id', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class CategorySerializer(serializers.ModelSerializer):
    """Сериализатор для категорий"""
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'business', 'parent', 'color', 'keywords']
    
    def to_representation(self, instance):
        """Кастомное представление с названием родительской категории"""
        representation = super().to_representation(instance)
        if instance.parent:
            representation['parent_name'] = instance.parent.name
        return representation


class ReceiptItemSerializer(serializers.ModelSerializer):
    """Сериализатор для позиций в чеке"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = ReceiptItem
        fields = [
            'id', 'name', 'quantity', 'price', 'total', 
            'category', 'category_name', 'category_confidence'
        ]


class ReceiptSerializer(serializers.ModelSerializer):
    """Сериализатор для чеков"""
    items = ReceiptItemSerializer(many=True, read_only=True)
    business_name = serializers.CharField(source='business.name', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Receipt
        fields = [
            'id', 'business', 'business_name', 'user', 'user_username',
            'receipt_number', 'receipt_date', 'total_amount', 'seller_name',
            'seller_inn', 'seller_address', 'status', 'ocr_text',
            'ocr_confidence', 'image', 'onec_document_id', 'onec_synced',
            'created_at', 'updated_at', 'items'
        ]
        read_only_fields = [
            'created_at', 'updated_at', 'ocr_text', 'ocr_confidence',
            'onec_document_id', 'onec_synced'
        ]


class BudgetSerializer(serializers.ModelSerializer):
    """Сериализатор для бюджетов"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Budget
        fields = [
            'id', 'business', 'category', 'category_name', 'period',
            'amount', 'start_date', 'end_date', 'notify_at_80', 'notify_at_100'
        ]


class FinancialRecommendationSerializer(serializers.ModelSerializer):
    """Сериализатор для финансовых рекомендаций"""
    business_name = serializers.CharField(source='business.name', read_only=True)
    related_categories_names = serializers.SerializerMethodField()
    
    class Meta:
        model = FinancialRecommendation
        fields = [
            'id', 'business', 'business_name', 'title', 'description',
            'recommendation_type', 'priority', 'status', 'related_categories',
            'related_categories_names', 'estimated_savings', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_related_categories_names(self, obj):
        """Получение названий связанных категорий"""
        return [cat.name for cat in obj.related_categories.all()]


class TelegramUserSerializer(serializers.ModelSerializer):
    """Сериализатор для пользователей Telegram"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = TelegramUser
        fields = [
            'id', 'user', 'user_username', 'telegram_id', 'username',
            'first_name', 'last_name', 'notifications_enabled', 'daily_summary',
            'budget_alerts', 'last_activity', 'total_receipts'
        ]
        read_only_fields = ['last_activity', 'total_receipts']


class ReceiptCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания чека"""
    
    class Meta:
        model = Receipt
        fields = [
            'business', 'receipt_number', 'receipt_date', 'total_amount',
            'seller_name', 'seller_inn', 'seller_address', 'image'
        ]
    
    def validate_total_amount(self, value):
        """Валидация суммы чека"""
        if value <= 0:
            raise serializers.ValidationError("Сумма чека должна быть больше нуля")
        if value > 1000000:
            raise serializers.ValidationError("Сумма чека слишком большая")
        return value
    
    def validate_receipt_date(self, value):
        """Валидация даты чека"""
        from django.utils import timezone
        
        if value > timezone.now():
            raise serializers.ValidationError("Дата чека не может быть в будущем")
        
        # Проверяем что чек не старше 5 лет
        five_years_ago = timezone.now() - timezone.timedelta(days=5*365)
        if value < five_years_ago:
            raise serializers.ValidationError("Чек не может быть старше 5 лет")
        
        return value


class CategoryCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания категории"""
    
    class Meta:
        model = Category
        fields = ['name', 'business', 'parent', 'color', 'keywords']
    
    def validate_name(self, value):
        """Валидация названия категории"""
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Название категории должно содержать минимум 2 символа")
        return value.strip()
    
    def validate_keywords(self, value):
        """Валидация ключевых слов"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Ключевые слова должны быть списком")
        
        # Фильтруем пустые строки
        filtered_keywords = [kw.strip() for kw in value if kw.strip()]
        
        if len(filtered_keywords) > 20:
            raise serializers.ValidationError("Максимальное количество ключевых слов - 20")
        
        return filtered_keywords


class BudgetCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания бюджета"""
    
    class Meta:
        model = Budget
        fields = [
            'business', 'category', 'period', 'amount', 
            'start_date', 'end_date', 'notify_at_80', 'notify_at_100'
        ]
    
    def validate(self, data):
        """Валидация бюджета"""
        if data['start_date'] >= data['end_date']:
            raise serializers.ValidationError("Дата начала должна быть раньше даты окончания")
        
        if data['amount'] <= 0:
            raise serializers.ValidationError("Сумма бюджета должна быть больше нуля")
        
        # Проверяем уникальность бюджета для категории и периода
        existing_budget = Budget.objects.filter(
            business=data['business'],
            category=data['category'],
            period=data['period'],
            start_date=data['start_date']
        ).exclude(id=self.instance.id if self.instance else None)
        
        if existing_budget.exists():
            raise serializers.ValidationError(
                "Бюджет для данной категории и периода уже существует"
            )
        
        return data
