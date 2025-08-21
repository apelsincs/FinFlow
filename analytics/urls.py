"""
FinFlow - URL-маршруты Analytics модуля
"""

from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('reports/monthly/', views.MonthlyReportView.as_view(), name='monthly-report'),
    path('reports/category/', views.CategoryReportView.as_view(), name='category-report'),
    path('trends/', views.TrendsView.as_view(), name='trends'),
]
