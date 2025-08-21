"""
FinFlow - Views для Analytics модуля
"""

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes

from core.services import AnalyticsService


class DashboardView(generics.GenericAPIView):
    """API для получения данных дашборда"""
    permission_classes = [IsAuthenticated]
    
    async def get(self, request):
        """Получение данных для дашборда"""
        try:
            analytics_service = AnalyticsService()
            
            # Получаем ежедневную сводку
            daily_summary = await analytics_service.get_daily_summary(request.user.id)
            
            # Получаем месячный отчет
            monthly_report = await analytics_service.get_monthly_report(request.user.id)
            
            return Response({
                'daily_summary': daily_summary,
                'monthly_report': monthly_report,
                'user_id': request.user.id
            })
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MonthlyReportView(generics.GenericAPIView):
    """API для получения месячного отчета"""
    permission_classes = [IsAuthenticated]
    
    async def get(self, request):
        """Получение месячного отчета"""
        try:
            analytics_service = AnalyticsService()
            report = await analytics_service.get_monthly_report(request.user.id)
            
            return Response(report)
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CategoryReportView(generics.GenericAPIView):
    """API для получения отчета по категориям"""
    permission_classes = [IsAuthenticated]
    
    async def get(self, request):
        """Получение отчета по категориям"""
        try:
            # TODO: Реализовать детальный отчет по категориям
            return Response({
                'message': 'Отчет по категориям находится в разработке'
            })
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TrendsView(generics.GenericAPIView):
    """API для получения трендов расходов"""
    permission_classes = [IsAuthenticated]
    
    async def get(self, request):
        """Получение трендов расходов"""
        try:
            # TODO: Реализовать анализ трендов
            return Response({
                'message': 'Анализ трендов находится в разработке'
            })
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_data(request):
    """API для экспорта данных"""
    try:
        # TODO: Реализовать экспорт данных в Excel/CSV
        return Response({
            'message': 'Экспорт данных находится в разработке'
        })
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
