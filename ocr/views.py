"""
FinFlow - Views для OCR модуля
"""

from rest_framework import generics, status, serializers
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser

from .services import OCRService


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


class ProcessReceiptView(generics.GenericAPIView):
    """API для обработки изображения чека"""
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]
    serializer_class = ReceiptImageSerializer
    
    async def post(self, request):
        """Обработка загруженного изображения чека"""
        try:
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                image_file = serializer.validated_data['image']
                
                # Сохраняем изображение во временную директорию
                import tempfile
                import os
                
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                    for chunk in image_file.chunks():
                        temp_file.write(chunk)
                    temp_path = temp_file.name
                
                try:
                    # Обрабатываем изображение через OCR
                    ocr_service = OCRService()
                    result = await ocr_service.process_receipt(temp_path)
                    
                    # Удаляем временный файл
                    os.unlink(temp_path)
                    
                    return Response({
                        'success': True,
                        'data': result
                    })
                    
                except Exception as e:
                    # Удаляем временный файл в случае ошибки
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                    raise e
            else:
                return Response(
                    serializer.errors, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OCRStatusView(generics.GenericAPIView):
    """API для проверки статуса OCR задачи"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Получение статуса OCR задачи"""
        # TODO: Реализовать проверку статуса асинхронной задачи
        return Response({
            'task_id': 'test',
            'status': 'completed',
            'message': 'OCR задача завершена'
        })
