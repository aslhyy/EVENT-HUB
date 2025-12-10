from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError, NotFound, PermissionDenied
from django.http import Http404
from django.core.exceptions import ObjectDoesNotExist
import logging

logger = logging.getLogger('apps')


def custom_exception_handler(exc, context):
    """
    Custom exception handler for DRF that provides consistent error responses
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    # Log the exception
    logger.error(f"Exception occurred: {exc.__class__.__name__} - {str(exc)}")

    if response is not None:
        # Standardize error response format
        custom_response_data = {
            'success': False,
            'error': {
                'code': response.status_code,
                'message': get_error_message(exc),
                'details': response.data
            }
        }
        response.data = custom_response_data

    # Handle specific Django exceptions that aren't caught by DRF
    elif isinstance(exc, Http404) or isinstance(exc, ObjectDoesNotExist):
        from rest_framework.response import Response
        from rest_framework import status
        
        response = Response(
            {
                'success': False,
                'error': {
                    'code': status.HTTP_404_NOT_FOUND,
                    'message': 'Recurso no encontrado',
                    'details': {'detail': str(exc)}
                }
            },
            status=status.HTTP_404_NOT_FOUND
        )

    return response


def get_error_message(exc):
    """
    Generate user-friendly error messages
    """
    error_messages = {
        'ValidationError': 'Error de validación en los datos proporcionados',
        'NotFound': 'El recurso solicitado no fue encontrado',
        'PermissionDenied': 'No tienes permisos para realizar esta acción',
        'AuthenticationFailed': 'Credenciales de autenticación inválidas',
        'NotAuthenticated': 'Debes iniciar sesión para acceder a este recurso',
        'MethodNotAllowed': 'Método HTTP no permitido para este endpoint',
        'ParseError': 'Error al procesar los datos enviados',
        'Throttled': 'Demasiadas solicitudes. Intenta más tarde',
    }
    
    exc_class = exc.__class__.__name__
    return error_messages.get(exc_class, 'Ha ocurrido un error en el servidor')