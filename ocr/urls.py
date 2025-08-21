"""
FinFlow - URL-маршруты OCR модуля
"""

from django.urls import path
from . import views

app_name = 'ocr'

urlpatterns = [
    path('process/', views.ProcessReceiptView.as_view(), name='process-receipt'),
    path('status/<str:task_id>/', views.OCRStatusView.as_view(), name='ocr-status'),
]
