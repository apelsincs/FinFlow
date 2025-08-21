"""
FinFlow - URL-маршруты Integrations модуля
"""

from django.urls import path
from . import views

app_name = 'integrations'

urlpatterns = [
    path('onec/sync/', views.OneCSyncView.as_view(), name='onec-sync'),
    path('onec/status/', views.OneCStatusView.as_view(), name='onec-status'),
    path('onec/companies/', views.OneCCompaniesView.as_view(), name='onec-companies'),
]
