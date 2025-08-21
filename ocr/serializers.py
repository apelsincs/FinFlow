"""
FinFlow - Сериализаторы для OCR модуля
"""

from rest_framework import serializers


class ReceiptImageSerializer(serializers.Serializer):
    """Сериализатор для загрузки изображения чека"""
    image = serializers.ImageField(
        max_length=None,
        allow_empty_file=False,
        use_url=False
    )
    
    def validate_image(self, value):
        """Валидация загруженного изображения"""
        # Проверяем размер файла (максимум 10MB)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("Размер изображения не должен превышать 10MB")
        
        # Проверяем формат
        allowed_formats = ['JPEG', 'JPG', 'PNG']
        if value.image.format not in allowed_formats:
            raise serializers.ValidationError(
                f"Поддерживаются только форматы: {', '.join(allowed_formats)}"
            )
        
        return value


class OCRResultSerializer(serializers.Serializer):
    """Сериализатор для результата OCR обработки"""
    text = serializers.CharField(help_text="Распознанный текст")
    confidence = serializers.FloatField(help_text="Уверенность распознавания")
    extracted_data = serializers.DictField(help_text="Извлеченные структурированные данные")
    processing_time = serializers.CharField(help_text="Время обработки")
    error = serializers.CharField(required=False, help_text="Описание ошибки если есть")


class ReceiptDataSerializer(serializers.Serializer):
    """Сериализатор для данных чека"""
    total_amount = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        required=False,
        help_text="Общая сумма чека"
    )
    receipt_number = serializers.CharField(
        required=False,
        help_text="Номер чека"
    )
    seller_name = serializers.CharField(
        required=False,
        help_text="Название продавца"
    )
    seller_inn = serializers.CharField(
        required=False,
        help_text="ИНН продавца"
    )
    receipt_date = serializers.DateTimeField(
        required=False,
        help_text="Дата чека"
    )
