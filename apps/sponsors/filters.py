import django_filters
from .models import Sponsor, Sponsorship


class SponsorFilter(django_filters.FilterSet):
    """Filtros avanzados para patrocinadores"""
    
    # Filtros por nombre e industria
    name = django_filters.CharFilter(
        field_name='name',
        lookup_expr='icontains'
    )
    industry = django_filters.CharFilter(
        field_name='industry',
        lookup_expr='icontains'
    )
    
    # Filtros por tier
    tier = django_filters.NumberFilter(field_name='tier__id')
    tier_name = django_filters.CharFilter(
        field_name='tier__name',
        lookup_expr='icontains'
    )
    
    # Filtros por estado
    status = django_filters.ChoiceFilter(
        field_name='status',
        choices=Sponsor.STATUS_CHOICES
    )
    
    # Filtros booleanos
    is_active = django_filters.BooleanFilter(field_name='is_active')
    
    # Filtros por account manager
    account_manager = django_filters.NumberFilter(field_name='account_manager__id')
    
    # Filtro por eventos
    has_events = django_filters.BooleanFilter(
        method='filter_has_events',
        label='Tiene eventos asociados'
    )
    
    class Meta:
        model = Sponsor
        fields = ['name', 'industry', 'tier', 'status', 'is_active']
    
    def filter_has_events(self, queryset, name, value):
        """Filtrar sponsors con eventos"""
        if value:
            return queryset.filter(sponsorships__isnull=False).distinct()
        return queryset.filter(sponsorships__isnull=True)


class SponsorshipFilter(django_filters.FilterSet):
    """Filtros avanzados para patrocinios"""
    
    # Filtros por sponsor
    sponsor = django_filters.NumberFilter(field_name='sponsor__id')
    sponsor_name = django_filters.CharFilter(
        field_name='sponsor__name',
        lookup_expr='icontains'
    )
    
    # Filtros por evento
    event = django_filters.NumberFilter(field_name='event__id')
    event_title = django_filters.CharFilter(
        field_name='event__title',
        lookup_expr='icontains'
    )
    
    # Filtros por tier
    tier = django_filters.NumberFilter(field_name='tier__id')
    tier_name = django_filters.CharFilter(
        field_name='tier__name',
        lookup_expr='icontains'
    )
    
    # Filtros por monto
    contribution_amount_gte = django_filters.NumberFilter(
        field_name='contribution_amount',
        lookup_expr='gte'
    )
    contribution_amount_lte = django_filters.NumberFilter(
        field_name='contribution_amount',
        lookup_expr='lte'
    )
    
    # Filtros por estado de pago
    payment_status = django_filters.ChoiceFilter(
        field_name='payment_status',
        choices=Sponsorship.PAYMENT_STATUS_CHOICES
    )
    
    # Filtros booleanos
    is_active = django_filters.BooleanFilter(field_name='is_active')
    is_public = django_filters.BooleanFilter(field_name='is_public')
    
    # Filtros por fechas
    contract_signed_date_gte = django_filters.DateFilter(
        field_name='contract_signed_date',
        lookup_expr='gte'
    )
    contract_signed_date_lte = django_filters.DateFilter(
        field_name='contract_signed_date',
        lookup_expr='lte'
    )
    
    # Filtros personalizados
    payment_overdue = django_filters.BooleanFilter(
        method='filter_payment_overdue',
        label='Pagos vencidos'
    )
    
    class Meta:
        model = Sponsorship
        fields = ['sponsor', 'event', 'tier', 'payment_status', 'is_active']
    
    def filter_payment_overdue(self, queryset, name, value):
        """Filtrar patrocinios con pagos vencidos"""
        if value:
            from django.utils import timezone
            today = timezone.now().date()
            
            return queryset.filter(
                payment_due_date__lt=today,
                payment_status__in=['pending', 'partial']
            )
        return queryset