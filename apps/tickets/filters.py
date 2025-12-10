import django_filters
from .models import TicketType, Ticket


class TicketTypeFilter(django_filters.FilterSet):
    """Filtros avanzados para tipos de tickets"""
    
    # Filtros por evento
    event = django_filters.NumberFilter(field_name='event__id')
    event_title = django_filters.CharFilter(
        field_name='event__title',
        lookup_expr='icontains'
    )
    
    # Filtros por nombre
    name = django_filters.CharFilter(
        field_name='name',
        lookup_expr='icontains'
    )
    
    # Filtros por precio
    price_gte = django_filters.NumberFilter(
        field_name='price',
        lookup_expr='gte'
    )
    price_lte = django_filters.NumberFilter(
        field_name='price',
        lookup_expr='lte'
    )
    
    # Filtros booleanos
    is_active = django_filters.BooleanFilter(field_name='is_active')
    includes_food = django_filters.BooleanFilter(field_name='includes_food')
    includes_drink = django_filters.BooleanFilter(field_name='includes_drink')
    includes_parking = django_filters.BooleanFilter(field_name='includes_parking')
    
    # Filtros por disponibilidad
    available = django_filters.BooleanFilter(
        method='filter_available',
        label='Disponible para venta'
    )
    
    class Meta:
        model = TicketType
        fields = ['event', 'name', 'is_active']
    
    def filter_available(self, queryset, name, value):
        """Filtrar tickets disponibles para la venta"""
        if value:
            from django.utils import timezone
            from django.db.models import F
            now = timezone.now()
            
            return queryset.filter(
                is_active=True,
                sale_start__lte=now,
                sale_end__gte=now,
                quantity_sold__lt=F('quantity_available')
            )
        return queryset


class TicketFilter(django_filters.FilterSet):
    """Filtros avanzados para tickets"""
    
    # Filtros por código
    ticket_code = django_filters.CharFilter(
        field_name='ticket_code',
        lookup_expr='icontains'
    )
    
    # Filtros por comprador
    buyer = django_filters.NumberFilter(field_name='buyer__id')
    buyer_username = django_filters.CharFilter(
        field_name='buyer__username',
        lookup_expr='icontains'
    )
    
    # Filtros por evento
    event = django_filters.NumberFilter(field_name='ticket_type__event__id')
    event_title = django_filters.CharFilter(
        field_name='ticket_type__event__title',
        lookup_expr='icontains'
    )
    
    # Filtros por tipo de ticket
    ticket_type = django_filters.NumberFilter(field_name='ticket_type__id')
    ticket_type_name = django_filters.CharFilter(
        field_name='ticket_type__name',
        lookup_expr='icontains'
    )
    
    # Filtros por estado
    status = django_filters.ChoiceFilter(
        field_name='status',
        choices=Ticket.STATUS_CHOICES
    )
    
    # Filtros booleanos
    is_active = django_filters.BooleanFilter(field_name='is_active')
    
    # Filtros por fechas
    purchase_date_gte = django_filters.DateTimeFilter(
        field_name='purchase_date',
        lookup_expr='gte'
    )
    purchase_date_lte = django_filters.DateTimeFilter(
        field_name='purchase_date',
        lookup_expr='lte'
    )
    
    # Filtros por precio
    final_price_gte = django_filters.NumberFilter(
        field_name='final_price',
        lookup_expr='gte'
    )
    final_price_lte = django_filters.NumberFilter(
        field_name='final_price',
        lookup_expr='lte'
    )
    
    class Meta:
        model = Ticket
        fields = ['status', 'is_active', 'buyer']