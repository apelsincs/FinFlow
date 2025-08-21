"""
FinFlow - Views для Bot модуля
"""

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes

from django.conf import settings
from django.http import HttpResponse


class TelegramWebhookView(generics.GenericAPIView):
    """Webhook для Telegram Bot"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Обработка webhook от Telegram"""
        try:
            # TODO: Реализовать обработку webhook
            return HttpResponse('OK')
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BotStatusView(generics.GenericAPIView):
    """API для проверки статуса бота"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Получение статуса бота"""
        try:
            return Response({
                'status': 'running',
                'bot_token': bool(settings.TELEGRAM_BOT_TOKEN),
                'webhook_url': settings.TELEGRAM_WEBHOOK_URL or 'Not set'
            })
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def set_webhook(request):
    """Установка webhook для Telegram Bot"""
    try:
        # TODO: Реализовать установку webhook
        return Response({
            'message': 'Webhook установлен',
            'status': 'success'
        })
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
