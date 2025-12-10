from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Q, Count

from .models import Category, Venue, Event
from .serializers import (
    CategorySerializer, VenueSerializer,
    EventListSerializer, EventDetailSerializer, EventStatsSerializer
)
from .filters import EventFilter, VenueFilter
from config.permissions import IsOrganizerOrReadOnly, IsAdminOrReadOnly


class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar categorías de eventos
    
    list: Listar todas las categorías activas
    retrieve: Obtener detalle de una categoría
    create: Crear nueva categoría (solo admin)
    update: Actualizar categoría (solo admin)
    destroy: Eliminar categoría (solo admin)
    """
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    @action(detail=True, methods=['get'])
    def events(self, request, pk=None):
        """
        Endpoint personalizado: Obtener eventos de una categoría
        GET /api/categories/{id}/events/
        """
        category = self.get_object()
        events = category.events.filter(
            is_published=True,
            status='published'
        ).order_by('-start_date')
        
        serializer = EventListSerializer(events, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def popular(self, request):
        """
        Endpoint personalizado: Categorías más populares
        GET /api/categories/popular/
        """
        categories = Category.objects.filter(
            is_active=True
        ).annotate(
            events_count=Count('events', filter=Q(events__is_published=True))
        ).order_by('-events_count')[:10]
        
        serializer = self.get_serializer(categories, many=True)
        return Response(serializer.data)


class VenueViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar lugares de eventos
    
    list: Listar todos los lugares
    retrieve: Obtener detalle de un lugar
    create: Crear nuevo lugar
    update: Actualizar lugar
    destroy: Eliminar lugar
    """
    queryset = Venue.objects.filter(is_active=True)
    serializer_class = VenueSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = VenueFilter
    search_fields = ['name', 'city', 'address']
    ordering_fields = ['name', 'city', 'capacity', 'created_at']
    ordering = ['name']
    
    @action(detail=True, methods=['get'])
    def upcoming_events(self, request, pk=None):
        """
        Endpoint personalizado: Eventos próximos en este lugar
        GET /api/venues/{id}/upcoming_events/
        """
        venue = self.get_object()
        now = timezone.now()
        
        events = venue.events.filter(
            is_published=True,
            status='published',
            start_date__gte=now
        ).order_by('start_date')
        
        serializer = EventListSerializer(events, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_city(self, request):
        """
        Endpoint personalizado: Lugares agrupados por ciudad
        GET /api/venues/by_city/
        """
        from django.db.models import Count
        
        cities = Venue.objects.filter(
            is_active=True
        ).values('city', 'state').annotate(
            venues_count=Count('id')
        ).order_by('-venues_count')
        
        return Response(cities)
    
    @action(detail=True, methods=['get'])
    def availability(self, request, pk=None):
        """
        Endpoint personalizado: Verificar disponibilidad del lugar
        GET /api/venues/{id}/availability/?start_date=2024-12-01&end_date=2024-12-02
        """
        venue = self.get_object()
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date or not end_date:
            return Response(
                {'error': 'Debe proporcionar start_date y end_date'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar eventos en ese rango
        conflicting_events = venue.events.filter(
            Q(start_date__range=[start_date, end_date]) |
            Q(end_date__range=[start_date, end_date]),
            status__in=['published', 'ongoing']
        )
        
        is_available = not conflicting_events.exists()
        
        return Response({
            'is_available': is_available,
            'conflicting_events': EventListSerializer(
                conflicting_events, many=True
            ).data if not is_available else []
        })


class EventViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar eventos
    
    list: Listar eventos publicados
    retrieve: Obtener detalle de un evento
    create: Crear nuevo evento
    update: Actualizar evento (solo organizador)
    destroy: Eliminar evento (solo organizador)
    """
    queryset = Event.objects.filter(is_published=True).select_related(
        'category', 'venue', 'organizer'
    ).prefetch_related('ticket_types', 'attendees')
    permission_classes = [IsOrganizerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = EventFilter
    search_fields = ['title', 'description', 'tags']
    ordering_fields = ['start_date', 'created_at', 'views_count']
    ordering = ['-start_date']
    
    def get_serializer_class(self):
        """Usar serializer diferente según la acción"""
        if self.action == 'list':
            return EventListSerializer
        elif self.action in ['stats', 'my_stats']:
            return EventStatsSerializer
        return EventDetailSerializer
    
    def get_queryset(self):
        """Personalizar queryset según el usuario"""
        queryset = super().get_queryset()
        user = self.request.user
        
        # Si es staff o si está en my_events, mostrar todos los estados
        if self.action == 'my_events' and user.is_authenticated:
            return Event.objects.filter(organizer=user).select_related(
                'category', 'venue'
            )
        
        # Por defecto, solo eventos publicados
        return queryset.filter(status='published')
    
    def retrieve(self, request, *args, **kwargs):
        """Incrementar contador de vistas al ver detalle"""
        instance = self.get_object()
        instance.views_count += 1
        instance.save(update_fields=['views_count'])
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """
        Endpoint personalizado: Eventos destacados
        GET /api/events/featured/
        """
        events = self.get_queryset().filter(
            is_featured=True,
            status='published'
        ).order_by('-start_date')[:10]
        
        serializer = EventListSerializer(events, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """
        Endpoint personalizado: Eventos próximos
        GET /api/events/upcoming/
        """
        now = timezone.now()
        events = self.get_queryset().filter(
            start_date__gte=now,
            status='published'
        ).order_by('start_date')[:20]
        
        serializer = EventListSerializer(events, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticatedOrReadOnly])
    def my_events(self, request):
        """
        Endpoint personalizado: Mis eventos organizados
        GET /api/events/my_events/
        """
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Debe iniciar sesión'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        events = self.get_queryset()
        serializer = EventListSerializer(events, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsOrganizerOrReadOnly])
    def publish(self, request, pk=None):
        """
        Endpoint personalizado: Publicar evento
        POST /api/events/{id}/publish/
        """
        event = self.get_object()
        
        # Validar que el usuario es el organizador
        if event.organizer != request.user and not request.user.is_staff:
            return Response(
                {'error': 'No tiene permisos para publicar este evento'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        event.is_published = True
        event.status = 'published'
        event.published_at = timezone.now()
        event.save()
        
        serializer = self.get_serializer(event)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """
        Endpoint personalizado: Estadísticas del evento
        GET /api/events/{id}/stats/
        """
        event = self.get_object()
        serializer = EventStatsSerializer(event)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def search_advanced(self, request):
        """
        Endpoint personalizado: Búsqueda avanzada
        GET /api/events/search_advanced/?q=music&city=Bogotá&date_from=2024-12-01
        """
        queryset = self.get_queryset()
        
        # Búsqueda por texto
        query = request.query_params.get('q', '')
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(tags__icontains=query)
            )
        
        # Filtro por ciudad
        city = request.query_params.get('city', '')
        if city:
            queryset = queryset.filter(venue__city__icontains=city)
        
        # Filtro por rango de fechas
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(start_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(start_date__lte=date_to)
        
        # Filtro por precio
        is_free = request.query_params.get('is_free')
        if is_free == 'true':
            queryset = queryset.filter(is_free=True)
        
        serializer = EventListSerializer(queryset, many=True)
        return Response(serializer.data)