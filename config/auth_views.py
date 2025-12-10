"""
Vistas de autenticación personalizadas
Ubicación: config/auth_views.py
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.tokens import RefreshToken
from config.utils.email_utils import EmailService
import logging

logger = logging.getLogger('apps')


@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """
    Endpoint para registrar nuevos usuarios
    POST /api/auth/register/
    """
    try:
        # Validar datos requeridos
        required_fields = ['username', 'email', 'password', 'first_name', 'last_name']
        for field in required_fields:
            if field not in request.data:
                return Response(
                    {'error': f'El campo {field} es requerido'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Validar que el username no exista
        if User.objects.filter(username=request.data['username']).exists():
            return Response(
                {'error': 'Este nombre de usuario ya está en uso'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar que el email no exista
        if User.objects.filter(email=request.data['email']).exists():
            return Response(
                {'error': 'Este email ya está registrado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Crear usuario
        user = User.objects.create(
            username=request.data['username'],
            email=request.data['email'],
            first_name=request.data['first_name'],
            last_name=request.data['last_name'],
            password=make_password(request.data['password'])
        )
        
        # Enviar email de bienvenida
        try:
            EmailService.send_welcome_email(user)
        except Exception as e:
            logger.error(f"Error enviando email de bienvenida: {str(e)}")
        
        # Generar tokens JWT
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'message': 'Usuario registrado exitosamente',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error en registro: {str(e)}")
        return Response(
            {'error': 'Error al crear usuario'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_user(request):
    """
    Obtiene información del usuario actual
    GET /api/auth/me/
    """
    user = request.user
    return Response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
        'date_joined': user.date_joined,
    })


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """
    Actualiza el perfil del usuario
    PUT/PATCH /api/auth/profile/
    """
    user = request.user
    
    # Actualizar campos permitidos
    allowed_fields = ['first_name', 'last_name', 'email']
    for field in allowed_fields:
        if field in request.data:
            setattr(user, field, request.data[field])
    
    # Cambiar contraseña si se proporciona
    if 'password' in request.data:
        user.password = make_password(request.data['password'])
    
    user.save()
    
    return Response({
        'message': 'Perfil actualizado exitosamente',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
        }
    })