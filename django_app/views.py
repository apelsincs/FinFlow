"""
FinFlow - API Views для Django приложения
"""

from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from .models import Receipt, Category, FinancialRecommendation
from .serializers import (
    ReceiptSerializer, CategorySerializer, 
    FinancialRecommendationSerializer
)
from core.services import AnalyticsService


class ReceiptListView(generics.ListCreateAPIView):
    """API для списка и создания чеков"""
    serializer_class = ReceiptSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Receipt.objects.filter(user=self.request.user).order_by('-receipt_date')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ReceiptDetailView(generics.RetrieveUpdateDestroyAPIView):
    """API для просмотра, редактирования и удаления чека"""
    serializer_class = ReceiptSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Receipt.objects.filter(user=self.request.user)


class CategoryListView(generics.ListCreateAPIView):
    """API для списка и создания категорий"""
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Category.objects.filter(business__owner=self.request.user)


class FinancialRecommendationListView(generics.ListAPIView):
    """API для списка финансовых рекомендаций"""
    serializer_class = FinancialRecommendationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return FinancialRecommendation.objects.filter(
            business__owner=self.request.user
        ).order_by('-priority', '-created_at')


class AnalyticsSummaryView(generics.GenericAPIView):
    """API для получения аналитической сводки"""
    permission_classes = [IsAuthenticated]
    
    async def get(self, request):
        """Получение ежедневной сводки"""
        analytics_service = AnalyticsService()
        summary = await analytics_service.get_daily_summary(request.user.id)
        return Response(summary)


class AnalyticsMonthlyView(generics.GenericAPIView):
    """API для получения месячного отчета"""
    permission_classes = [IsAuthenticated]
    
    async def get(self, request):
        """Получение месячного отчета"""
        analytics_service = AnalyticsService()
        report = await analytics_service.get_monthly_report(request.user.id)
        return Response(report)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """Получение статистики для дашборда"""
    user = request.user
    
    # Общая статистика
    total_receipts = Receipt.objects.filter(user=user).count()
    total_spent = Receipt.objects.filter(user=user).aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    # Статистика за текущий месяц
    from django.utils import timezone
    from datetime import timedelta
    
    now = timezone.now()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    monthly_receipts = Receipt.objects.filter(
        user=user,
        receipt_date__gte=start_of_month
    )
    
    monthly_count = monthly_receipts.count()
    monthly_spent = monthly_receipts.aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    return Response({
        'total_receipts': total_receipts,
        'total_spent': total_spent,
        'monthly_receipts': monthly_count,
        'monthly_spent': monthly_spent,
        'current_month': start_of_month.strftime('%B %Y')
    })
