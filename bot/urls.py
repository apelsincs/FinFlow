"""
FinFlow - URL-маршруты Bot модуля
"""

from django.urls import path
from . import views

app_name = 'bot'

urlpatterns = [
    path('webhook/', views.TelegramWebhookView.as_view(), name='webhook'),
    path('status/', views.BotStatusView.as_view(), name='status'),
]
