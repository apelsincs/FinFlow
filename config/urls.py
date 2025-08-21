"""
FinFlow - Основные URL-маршруты Django приложения
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Админ-панель Django
    path('admin/', admin.site.urls),
    
    # API endpoints для основных приложений
    path('api/', include('django_app.urls')),
    path('api/ocr/', include('ocr.urls')),
    path('api/analytics/', include('analytics.urls')),
    path('api/integrations/', include('integrations.urls')),
    
    # Telegram webhook для бота
    path('webhook/telegram/', include('bot.urls')),
]

# Добавляем статические и медиа файлы в режиме разработки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Настройка заголовков админ-панели
admin.site.site_header = "FinFlow - Администрирование"
admin.site.site_title = "FinFlow Admin"
admin.site.index_title = "Добро пожаловать в FinFlow"
