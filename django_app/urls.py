"""
FinFlow - URL-маршруты Django приложения
"""

from django.urls import path
from . import views

app_name = 'django_app'

urlpatterns = [
    # API endpoints для основных функций
    path('receipts/', views.ReceiptListView.as_view(), name='receipt-list'),
    path('receipts/<int:pk>/', views.ReceiptDetailView.as_view(), name='receipt-detail'),
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('analytics/summary/', views.AnalyticsSummaryView.as_view(), name='analytics-summary'),
    path('analytics/monthly/', views.AnalyticsMonthlyView.as_view(), name='analytics-monthly'),
    path('recommendations/', views.FinancialRecommendationListView.as_view(), name='recommendation-list'),
]
