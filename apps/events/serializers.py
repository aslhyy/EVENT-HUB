from rest_framework import serializers
from django.utils import timezone
from .models import Category, Venue, Event


class CategorySerializer(serializers.ModelSerializer):
    """Serializer para categorías de eventos"""
    events_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description', 'icon',
            'is_active', 'events_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['slug', 'created_at', 'updated_at']
    
    def get_events_count(self, obj):
        """Cuenta eventos activos de esta categoría"""
        return obj.events.filter(is_published=True, status='published').count()


class VenueSerializer(serializers.ModelSerializer):
    """Serializer para lugares de eventos"""
    full_address = serializers.SerializerMethodField()
    upcoming_events_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Venue
        fields = [
            'id', 'name', 'address', 'city', 'state', 'country',
            'postal_code', 'capacity', 'latitude', 'longitude',
            'facilities', 'contact_phone', 'contact_email',
            'full_address', 'upcoming_events_count',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_full_address(self, obj):
        """Dirección completa formateada"""
        return f"{obj.address}, {obj.city}, {obj.state}, {obj.country}"
    
    def get_upcoming_events_count(self, obj):
        """Cuenta eventos próximos en este lugar"""
        now = timezone.now()
        return obj.events.filter(
            is_published=True,
            start_date__gte=now,
            status='published'
        ).count()
    
    def validate_capacity(self, value):
        """Validar que la capacidad sea positiva"""
        if value < 1:
            raise serializers.ValidationError("La capacidad debe ser mayor a 0")
        return value
    
    def validate(self, data):
        """Validaciones cruzadas"""
        if data.get('latitude') and not data.get('longitude'):
            raise serializers.ValidationError(
                "Si proporciona latitud, debe proporcionar longitud"
            )
        if data.get('longitude') and not data.get('latitude'):
            raise serializers.ValidationError(
                "Si proporciona longitud, debe proporcionar latitud"
            )
        return data


class EventListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listado de eventos"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    venue_name = serializers.CharField(source='venue.name', read_only=True)
    venue_city = serializers.CharField(source='venue.city', read_only=True)
    organizer_name = serializers.CharField(source='organizer.username', read_only=True)
    available_spots = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()
    days_until_event = serializers.SerializerMethodField()
    
    class Meta:
        model = Event
        fields = [
            'id', 'title', 'slug', 'short_description',
            'category_name', 'venue_name', 'venue_city',
            'organizer_name', 'start_date', 'end_date',
            'is_free', 'max_attendees', 'available_spots',
            'thumbnail_image', 'status', 'is_featured',
            'is_published', 'is_active', 'views_count',
            'days_until_event', 'created_at'
        ]
    
    def get_days_until_event(self, obj):
        """Días restantes hasta el evento"""
        if obj.start_date > timezone.now():
            delta = obj.start_date - timezone.now()
            return delta.days
        return 0


class EventDetailSerializer(serializers.ModelSerializer):
    """Serializer detallado para eventos"""
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True
    )
    venue = VenueSerializer(read_only=True)
    venue_id = serializers.PrimaryKeyRelatedField(
        queryset=Venue.objects.all(),
        source='venue',
        write_only=True
    )
    organizer_name = serializers.CharField(source='organizer.username', read_only=True)
    organizer_email = serializers.EmailField(source='organizer.email', read_only=True)
    available_spots = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()
    
    # Estadísticas
    total_attendees = serializers.SerializerMethodField()
    total_tickets_sold = serializers.SerializerMethodField()
    ticket_types_count = serializers.SerializerMethodField()
    sponsors_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Event
        fields = [
            'id', 'title', 'slug', 'description', 'short_description',
            'category', 'category_id', 'venue', 'venue_id',
            'organizer_name', 'organizer_email',
            'start_date', 'end_date', 'registration_start', 'registration_end',
            'is_free', 'max_attendees', 'available_spots',
            'banner_image', 'thumbnail_image',
            'status', 'is_featured', 'is_published', 'is_active',
            'views_count', 'tags',
            'total_attendees', 'total_tickets_sold', 'ticket_types_count',
            'sponsors_count',
            'created_at', 'updated_at', 'published_at'
        ]
        read_only_fields = [
            'slug', 'views_count', 'created_at', 'updated_at', 'published_at'
        ]
    
    def get_total_attendees(self, obj):
        """Total de asistentes confirmados"""
        return obj.attendees.filter(status='confirmed').count()
    
    def get_total_tickets_sold(self, obj):
        """Total de tickets vendidos"""
        return sum(
            ticket_type.quantity_sold 
            for ticket_type in obj.ticket_types.all()
        )
    
    def get_ticket_types_count(self, obj):
        """Cantidad de tipos de tickets"""
        return obj.ticket_types.filter(is_active=True).count()
    
    def get_sponsors_count(self, obj):
        """Cantidad de patrocinadores"""
        return obj.sponsorships.filter(is_public=True).count()
    
    def validate(self, data):
        """Validaciones del evento"""
        # Validar fechas
        if 'start_date' in data and 'end_date' in data:
            if data['start_date'] >= data['end_date']:
                raise serializers.ValidationError(
                    "La fecha de inicio debe ser anterior a la fecha de fin"
                )
        
        if 'registration_start' in data and 'registration_end' in data:
            if data['registration_start'] >= data['registration_end']:
                raise serializers.ValidationError(
                    "El inicio de registro debe ser anterior al fin de registro"
                )
        
        if 'registration_end' in data and 'start_date' in data:
            if data['registration_end'] > data['start_date']:
                raise serializers.ValidationError(
                    "El registro debe finalizar antes del inicio del evento"
                )
        
        # Validar capacidad vs venue
        if 'max_attendees' in data and 'venue' in data:
            if data['max_attendees'] and data['max_attendees'] > data['venue'].capacity:
                raise serializers.ValidationError(
                    f"El máximo de asistentes ({data['max_attendees']}) "
                    f"excede la capacidad del lugar ({data['venue'].capacity})"
                )
        
        return data
    
    def create(self, validated_data):
        """Asignar el organizador automáticamente"""
        validated_data['organizer'] = self.context['request'].user
        return super().create(validated_data)


class EventStatsSerializer(serializers.ModelSerializer):
    """Serializer para estadísticas de eventos"""
    total_revenue = serializers.SerializerMethodField()
    total_attendees = serializers.SerializerMethodField()
    total_tickets_sold = serializers.SerializerMethodField()
    attendance_rate = serializers.SerializerMethodField()
    most_popular_ticket = serializers.SerializerMethodField()
    
    class Meta:
        model = Event
        fields = [
            'id', 'title', 'total_revenue', 'total_attendees',
            'total_tickets_sold', 'attendance_rate', 'most_popular_ticket'
        ]
    
    def get_total_revenue(self, obj):
        """Calcular ingresos totales por tickets"""
        from apps.tickets.models import Ticket
        tickets = Ticket.objects.filter(
            ticket_type__event=obj,
            status__in=['paid', 'confirmed', 'used']
        )
        return sum(ticket.final_price for ticket in tickets)
    
    def get_total_attendees(self, obj):
        """Total de asistentes registrados"""
        return obj.attendees.count()
    
    def get_total_tickets_sold(self, obj):
        """Total de tickets vendidos"""
        return sum(tt.quantity_sold for tt in obj.ticket_types.all())
    
    def get_attendance_rate(self, obj):
        """Tasa de asistencia (checked in vs confirmados)"""
        confirmed = obj.attendees.filter(status='confirmed').count()
        checked_in = obj.attendees.filter(status='checked_in').count()
        
        if confirmed == 0:
            return 0
        
        return round((checked_in / confirmed) * 100, 2)
    
    def get_most_popular_ticket(self, obj):
        """Tipo de ticket más vendido"""
        ticket_types = obj.ticket_types.order_by('-quantity_sold').first()
        if ticket_types:
            return {
                'name': ticket_types.name,
                'sold': ticket_types.quantity_sold
            }
        return None