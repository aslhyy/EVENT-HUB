from django.http import JsonResponse
from django.db import connection
from django.conf import settings
import logging

logger = logging.getLogger('apps')


def health_check(request):
    """
    Endpoint de health check para verificar el estado del servidor
    
    GET /health/
    GET /api/health/
    
    Verifica:
    - Conectividad a la base de datos
    - Estado del servidor
    - Configuración básica
    
    Returns:
        200 OK si todo está bien
        503 Service Unavailable si hay problemas
    """
    health_status = {
        'status': 'healthy',
        'service': 'EventHub API',
        'version': '1.0.0',
        'checks': {}
    }
    
    # Verificar conexión a la base de datos
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            health_status['checks']['database'] = {
                'status': 'healthy',
                'message': 'Database connection successful'
            }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status['status'] = 'unhealthy'
        health_status['checks']['database'] = {
            'status': 'unhealthy',
            'message': f'Database connection failed: {str(e)}'
        }
    
    # Verificar configuración
    health_status['checks']['configuration'] = {
        'status': 'healthy',
        'debug_mode': settings.DEBUG,
        'allowed_hosts': settings.ALLOWED_HOSTS,
    }
    
    # Verificar archivos estáticos y media
    try:
        import os
        media_exists = os.path.exists(settings.MEDIA_ROOT)
        static_exists = os.path.exists(settings.STATIC_ROOT) or settings.DEBUG
        
        health_status['checks']['file_system'] = {
            'status': 'healthy' if media_exists and static_exists else 'warning',
            'media_root': media_exists,
            'static_root': static_exists,
        }
    except Exception as e:
        health_status['checks']['file_system'] = {
            'status': 'warning',
            'message': str(e)
        }
    
    # Determinar código de estado HTTP
    status_code = 200 if health_status['status'] == 'healthy' else 503
    
    return JsonResponse(health_status, status=status_code)