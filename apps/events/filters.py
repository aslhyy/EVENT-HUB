import django_filters
from django.utils import timezone
from .models import Event, Venue


class EventFilter(django_filters.FilterSet):
    """Filtros avanzados para eventos"""
    
    # Filtros por texto
    title = django_filters.CharFilter(
        field_name='title',
        lookup_expr='icontains'
    )
    description = django_filters.CharFilter(
        field_name='description',
        lookup_expr='icontains'
    )
    
    # Filtros por categoría
    category = django_filters.NumberFilter(field_name='category__id')
    category_name = django_filters.CharFilter(
        field_name='category__name',
        lookup_expr='icontains'
    )
    
    # Filtros por lugar
    venue = django_filters.NumberFilter(field_name='venue__id')
    city = django_filters.CharFilter(
        field_name='venue__city',
        lookup_expr='icontains'
    )
    state = django_filters.CharFilter(
        field_name='venue__state',
        lookup_expr='icontains'
    )
    
    # Filtros por fechas
    start_date = django_filters.DateTimeFilter(
        field_name='start_date',
        lookup_expr='exact'
    )
    start_date_gte = django_filters.DateTimeFilter(
        field_name='start_date',
        lookup_expr='gte'
    )
    start_date_lte = django_filters.DateTimeFilter(
        field_name='start_date',
        lookup_expr='lte'
    )
    end_date = django_filters.DateTimeFilter(
        field_name='end_date',
        lookup_expr='exact'
    )
    end_date_gte = django_filters.DateTimeFilter(
        field_name='end_date',
        lookup_expr='gte'
    )
    end_date_lte = django_filters.DateTimeFilter(
        field_name='end_date',
        lookup_expr='lte'
    )
    
    # Filtros booleanos
    is_free = django_filters.BooleanFilter(field_name='is_free')
    is_featured = django_filters.BooleanFilter(field_name='is_featured')
    is_published = django_filters.BooleanFilter(field_name='is_published')
    
    # Filtros por estado
    status = django_filters.ChoiceFilter(
        field_name='status',
        choices=Event.STATUS_CHOICES
    )
    
    # Filtro por organizador
    organizer = django_filters.NumberFilter(field_name='organizer__id')
    organizer_username = django_filters.CharFilter(
        field_name='organizer__username',
        lookup_expr='icontains'
    )
    
    # Filtro por tags
    tags = django_filters.CharFilter(
        field_name='tags',
        lookup_expr='icontains'
    )
    
    # Filtro por capacidad
    max_attendees_gte = django_filters.NumberFilter(
        field_name='max_attendees',
        lookup_expr='gte'
    )
    max_attendees_lte = django_filters.NumberFilter(
        field_name='max_attendees',
        lookup_expr='lte'
    )
    
    # Filtros personalizados
    upcoming = django_filters.BooleanFilter(
        method='filter_upcoming',
        label='Eventos próximos'
    )
    past = django_filters.BooleanFilter(
        method='filter_past',
        label='Eventos pasados'
    )
    active = django_filters.BooleanFilter(
        method='filter_active',
        label='Eventos activos'
    )
    
    class Meta:
        model = Event
        fields = [
            'title', 'description', 'category', 'venue',
            'city', 'state', 'is_free', 'is_featured',
            'status', 'organizer', 'tags'
        ]
    
    def filter_upcoming(self, queryset, name, value):
        """Filtrar eventos próximos (futuro)"""
        if value:
            now = timezone.now()
            return queryset.filter(start_date__gte=now)
        return queryset
    
    def filter_past(self, queryset, name, value):
        """Filtrar eventos pasados"""
        if value:
            now = timezone.now()
            return queryset.filter(end_date__lt=now)
        return queryset
    
    def filter_active(self, queryset, name, value):
        """Filtrar eventos activos (en curso)"""
        if value:
            now = timezone.now()
            return queryset.filter(
                start_date__lte=now,
                end_date__gte=now,
                status='ongoing'
            )
        return queryset


class VenueFilter(django_filters.FilterSet):
    """Filtros avanzados para lugares"""
    
    # Filtros por texto
    name = django_filters.CharFilter(
        field_name='name',
        lookup_expr='icontains'
    )
    city = django_filters.CharFilter(
        field_name='city',
        lookup_expr='icontains'
    )
    state = django_filters.CharFilter(
        field_name='state',
        lookup_expr='icontains'
    )
    address = django_filters.CharFilter(
        field_name='address',
        lookup_expr='icontains'
    )
    
    # Filtros por capacidad
    capacity_gte = django_filters.NumberFilter(
        field_name='capacity',
        lookup_expr='gte'
    )
    capacity_lte = django_filters.NumberFilter(
        field_name='capacity',
        lookup_expr='lte'
    )
    
    # Filtro booleano
    is_active = django_filters.BooleanFilter(field_name='is_active')
    
    class Meta:
        model = Venue
        fields = ['name', 'city', 'state', 'is_active']