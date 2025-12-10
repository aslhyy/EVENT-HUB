import django_filters
from django.db.models import Q
from .models import Attendee


class AttendeeFilter(django_filters.FilterSet):
    """Filtros avanzados para asistentes"""
    
    # Filtros por nombre
    first_name = django_filters.CharFilter(
        field_name='first_name',
        lookup_expr='icontains'
    )
    last_name = django_filters.CharFilter(
        field_name='last_name',
        lookup_expr='icontains'
    )
    full_name = django_filters.CharFilter(
        method='filter_full_name',
        label='Nombre completo'
    )
    
    # Filtros por email y teléfono
    email = django_filters.CharFilter(
        field_name='email',
        lookup_expr='icontains'
    )
    phone = django_filters.CharFilter(
        field_name='phone',
        lookup_expr='icontains'
    )
    
    # Filtros por empresa
    company = django_filters.CharFilter(
        field_name='company',
        lookup_expr='icontains'
    )
    job_title = django_filters.CharFilter(
        field_name='job_title',
        lookup_expr='icontains'
    )
    
    # Filtros por evento
    event = django_filters.NumberFilter(field_name='event__id')
    event_title = django_filters.CharFilter(
        field_name='event__title',
        lookup_expr='icontains'
    )
    
    # Filtros por estado
    status = django_filters.ChoiceFilter(
        field_name='status',
        choices=Attendee.STATUS_CHOICES
    )
    
    # Filtros por fechas
    registration_date_gte = django_filters.DateTimeFilter(
        field_name='registration_date',
        lookup_expr='gte'
    )
    registration_date_lte = django_filters.DateTimeFilter(
        field_name='registration_date',
        lookup_expr='lte'
    )
    
    # Filtros booleanos
    receive_reminders = django_filters.BooleanFilter(field_name='receive_reminders')
    receive_updates = django_filters.BooleanFilter(field_name='receive_updates')
    
    # Filtros personalizados
    checked_in = django_filters.BooleanFilter(
        method='filter_checked_in',
        label='Ya hizo check-in'
    )
    has_ticket = django_filters.BooleanFilter(
        method='filter_has_ticket',
        label='Tiene ticket asociado'
    )
    
    class Meta:
        model = Attendee
        fields = ['event', 'status', 'email', 'company']
    
    def filter_full_name(self, queryset, name, value):
        """Filtrar por nombre completo"""
        return queryset.filter(
            Q(first_name__icontains=value) |
            Q(last_name__icontains=value)
        )
    
    def filter_checked_in(self, queryset, name, value):
        """Filtrar por check-in realizado"""
        if value:
            return queryset.filter(status='checked_in')
        return queryset.exclude(status='checked_in')
    
    def filter_has_ticket(self, queryset, name, value):
        """Filtrar por tener ticket asociado"""
        if value:
            return queryset.filter(ticket__isnull=False)
        return queryset.filter(ticket__isnull=True)