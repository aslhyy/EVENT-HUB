from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permiso personalizado para permitir solo a los propietarios editar objetos
    """
    def has_object_permission(self, request, view, obj):
        # Permisos de lectura para cualquiera
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Permisos de escritura solo para el propietario
        if hasattr(obj, 'organizer'):
            return obj.organizer == request.user
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'buyer'):
            return obj.buyer == request.user
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        
        return False


class IsOrganizerOrReadOnly(permissions.BasePermission):
    """
    Permiso para organizadores de eventos
    """
    def has_permission(self, request, view):
        # Lectura para todos
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Escritura solo para usuarios autenticados
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Lectura para todos
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Determinar el organizador según el tipo de objeto
        if hasattr(obj, 'organizer'):
            return obj.organizer == request.user or request.user.is_staff
        elif hasattr(obj, 'event') and hasattr(obj.event, 'organizer'):
            return obj.event.organizer == request.user or request.user.is_staff
        
        return request.user.is_staff


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permiso solo para administradores (escritura)
    Lectura para todos
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


class IsEventStaffOrReadOnly(permissions.BasePermission):
    """
    Permiso para staff de eventos (organizador o admin)
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Verificar si es organizador del evento relacionado
        event = None
        if hasattr(obj, 'event'):
            event = obj.event
        elif hasattr(obj, 'ticket_type') and hasattr(obj.ticket_type, 'event'):
            event = obj.ticket_type.event
        
        if event:
            return (
                event.organizer == request.user or
                request.user.is_staff
            )
        
        return request.user.is_staff


class CanCheckIn(permissions.BasePermission):
    """
    Permiso para realizar check-in de asistentes
    """
    def has_permission(self, request, view):
        # Solo usuarios autenticados pueden hacer check-in
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Staff siempre puede
        if request.user.is_staff:
            return True
        
        # Organizador del evento puede
        if hasattr(obj, 'event'):
            return obj.event.organizer == request.user
        
        return False


class IsSponsorManagerOrReadOnly(permissions.BasePermission):
    """
    Permiso para gestores de patrocinadores
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Staff siempre puede
        if request.user.is_staff:
            return True
        
        # Account manager puede editar su sponsor
        if hasattr(obj, 'account_manager'):
            return obj.account_manager == request.user
        
        # Para sponsorships, verificar el event organizer
        if hasattr(obj, 'event'):
            return obj.event.organizer == request.user
        
        return False


class IsTicketOwner(permissions.BasePermission):
    """
    Permiso para propietarios de tickets
    """
    def has_object_permission(self, request, view, obj):
        # El comprador puede ver su ticket
        if hasattr(obj, 'buyer'):
            return obj.buyer == request.user
        
        # El organizador del evento puede ver todos los tickets
        if hasattr(obj, 'ticket_type') and hasattr(obj.ticket_type, 'event'):
            event = obj.ticket_type.event
            return event.organizer == request.user or request.user.is_staff
        
        return request.user.is_staff


class CanManageSurvey(permissions.BasePermission):
    """
    Permiso para gestionar encuestas
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Staff siempre puede
        if request.user.is_staff:
            return True
        
        # Creador de la encuesta puede
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        
        # Organizador del evento puede
        if hasattr(obj, 'event'):
            return obj.event.organizer == request.user
        
        # Para respuestas, verificar la encuesta
        if hasattr(obj, 'survey'):
            return (
                obj.survey.created_by == request.user or
                obj.survey.event.organizer == request.user
            )
        
        return False