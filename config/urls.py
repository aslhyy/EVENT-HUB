from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from .views import health_check
from .auth_views import register_user, get_current_user, update_profile

# Configuración de Swagger
schema_view = get_schema_view(
    openapi.Info(
        title="EventHub API",
        default_version='v1',
        description="""
        # EventHub - Sistema de Gestión de Eventos
        
        API RESTful profesional para gestión de eventos, tickets, asistentes y patrocinadores.
        
        ## Características:
        - 🎉 Gestión completa de eventos
        - 🎫 Sistema de tickets y descuentos
        - 👥 Registro de asistentes
        - 💼 Gestión de patrocinadores
        - 🔐 Autenticación JWT
        
        ## Autenticación:
        Para usar endpoints protegidos, incluye el header:
        ```
        Authorization: Bearer {tu_token}
        ```
        
        Obtén tu token en `/api/token/`
        """,
        terms_of_service="https://www.eventhub.com/terms/",
        contact=openapi.Contact(email="contact@eventhub.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
    authentication_classes=[],
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Health check
    path('api/health/', health_check, name='health-check'),
    
    # Autenticación JWT
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Auth personalizado
    path('api/auth/register/', register_user, name='register'),
    path('api/auth/me/', get_current_user, name='current-user'),
    path('api/auth/profile/', update_profile, name='update-profile'),
    
    # Apps
    path('api/events/', include('apps.events.urls')),
    path('api/tickets/', include('apps.tickets.urls')),
    path('api/attendees/', include('apps.attendees.urls')),
    path('api/sponsors/', include('apps.sponsors.urls')),
    
    # Documentación API
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
]

# Servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)