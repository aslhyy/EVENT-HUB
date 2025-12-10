from rest_framework import serializers
from django.utils import timezone
from django.db import transaction
from .models import TicketType, Ticket, DiscountCode
from apps.events.models import Event


class TicketTypeSerializer(serializers.ModelSerializer):
    """Serializer para tipos de tickets"""
    event_title = serializers.CharField(source='event.title', read_only=True)
    quantity_remaining = serializers.ReadOnlyField()
    is_sold_out = serializers.ReadOnlyField()
    is_on_sale = serializers.ReadOnlyField()
    
    class Meta:
        model = TicketType
        fields = [
            'id', 'event', 'event_title', 'name', 'description',
            'price', 'quantity_available', 'quantity_sold',
            'quantity_remaining', 'is_sold_out', 'max_per_order',
            'sale_start', 'sale_end', 'is_active', 'is_on_sale',
            'includes_food', 'includes_drink', 'includes_parking',
            'includes_merchandise', 'benefits_description',
            'display_order', 'created_at', 'updated_at'
        ]
        read_only_fields = ['quantity_sold', 'created_at', 'updated_at']
    
    def validate(self, data):
        """Validaciones del tipo de ticket"""
        if 'sale_start' in data and 'sale_end' in data:
            if data['sale_start'] >= data['sale_end']:
                raise serializers.ValidationError(
                    "La fecha de inicio de ventas debe ser anterior a la fecha de fin"
                )
        
        if 'sale_end' in data and 'event' in data:
            if data['sale_end'] > data['event'].start_date:
                raise serializers.ValidationError(
                    "Las ventas deben finalizar antes del inicio del evento"
                )
        
        if 'max_per_order' in data and 'quantity_available' in data:
            if data['max_per_order'] > data['quantity_available']:
                raise serializers.ValidationError(
                    "El máximo por orden no puede exceder la cantidad disponible"
                )
        
        return data


class TicketListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listado de tickets"""
    event_title = serializers.CharField(source='ticket_type.event.title', read_only=True)
    ticket_type_name = serializers.CharField(source='ticket_type.name', read_only=True)
    buyer_name = serializers.CharField(source='buyer.username', read_only=True)
    
    class Meta:
        model = Ticket
        fields = [
            'id', 'ticket_code', 'event_title', 'ticket_type_name',
            'buyer_name', 'status', 'purchase_date', 'final_price'
        ]


class TicketDetailSerializer(serializers.ModelSerializer):
    """Serializer detallado para tickets"""
    ticket_type_detail = TicketTypeSerializer(source='ticket_type', read_only=True)
    buyer_info = serializers.SerializerMethodField()
    attendee_info = serializers.SerializerMethodField()
    event_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Ticket
        fields = [
            'id', 'ticket_code', 'qr_code', 'ticket_type',
            'ticket_type_detail', 'buyer', 'buyer_info',
            'attendee', 'attendee_info', 'event_info',
            'purchase_date', 'payment_method', 'transaction_id',
            'original_price', 'discount_applied', 'final_price',
            'status', 'is_active', 'used_at', 'cancelled_at',
            'cancellation_reason', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'ticket_code', 'qr_code', 'purchase_date',
            'created_at', 'updated_at'
        ]
    
    def get_buyer_info(self, obj):
        """Información del comprador"""
        return {
            'id': obj.buyer.id,
            'username': obj.buyer.username,
            'email': obj.buyer.email,
            'first_name': obj.buyer.first_name,
            'last_name': obj.buyer.last_name,
        }
    
    def get_attendee_info(self, obj):
        """Información del asistente"""
        if obj.attendee:
            return {
                'id': obj.attendee.id,
                'full_name': obj.attendee.full_name,
                'email': obj.attendee.email,
                'phone': obj.attendee.phone,
                'status': obj.attendee.status,
            }
        return None
    
    def get_event_info(self, obj):
        """Información del evento"""
        event = obj.ticket_type.event
        return {
            'id': event.id,
            'title': event.title,
            'start_date': event.start_date,
            'venue_name': event.venue.name,
            'venue_address': event.venue.address,
        }


class TicketPurchaseSerializer(serializers.Serializer):
    """Serializer para compra de tickets"""
    ticket_type_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)
    discount_code = serializers.CharField(required=False, allow_blank=True)
    payment_method = serializers.CharField(max_length=50)
    
    def validate_ticket_type_id(self, value):
        """Validar que el tipo de ticket existe"""
        try:
            ticket_type = TicketType.objects.get(id=value)
            if not ticket_type.is_on_sale:
                raise serializers.ValidationError(
                    "Este tipo de ticket no está disponible para la venta"
                )
        except TicketType.DoesNotExist:
            raise serializers.ValidationError("Tipo de ticket no encontrado")
        return value
    
    def validate(self, data):
        """Validaciones de la compra"""
        ticket_type = TicketType.objects.get(id=data['ticket_type_id'])
        quantity = data['quantity']
        
        # Validar cantidad disponible
        if ticket_type.quantity_remaining < quantity:
            raise serializers.ValidationError(
                f"Solo quedan {ticket_type.quantity_remaining} tickets disponibles"
            )
        
        # Validar máximo por orden
        if quantity > ticket_type.max_per_order:
            raise serializers.ValidationError(
                f"Solo puede comprar máximo {ticket_type.max_per_order} tickets por orden"
            )
        
        # Validar código de descuento si existe
        if 'discount_code' in data and data['discount_code']:
            try:
                discount = DiscountCode.objects.get(
                    code=data['discount_code'],
                    is_active=True
                )
                if not discount.is_valid:
                    raise serializers.ValidationError(
                        "El código de descuento no es válido o ha expirado"
                    )
                data['discount_object'] = discount
            except DiscountCode.DoesNotExist:
                raise serializers.ValidationError(
                    "Código de descuento no encontrado"
                )
        
        return data
    
    @transaction.atomic
    def create(self, validated_data):
        """Crear tickets con transacción atómica"""
        user = self.context['request'].user
        ticket_type = TicketType.objects.select_for_update().get(
            id=validated_data['ticket_type_id']
        )
        quantity = validated_data['quantity']
        discount_obj = validated_data.get('discount_object')
        
        # Calcular precios
        original_price = ticket_type.price
        discount_amount = 0
        
        if discount_obj:
            if discount_obj.discount_type == 'percentage':
                discount_amount = (original_price * discount_obj.discount_value) / 100
            else:
                discount_amount = discount_obj.discount_value
        
        final_price = original_price - discount_amount
        
        # Crear tickets
        tickets = []
        for _ in range(quantity):
            ticket = Ticket.objects.create(
                ticket_type=ticket_type,
                buyer=user,
                original_price=original_price,
                discount_applied=discount_amount,
                final_price=final_price,
                payment_method=validated_data['payment_method'],
                status='paid'
            )
            tickets.append(ticket)
        
        # Actualizar cantidad vendida
        ticket_type.quantity_sold += quantity
        ticket_type.save()
        
        # Actualizar código de descuento
        if discount_obj:
            discount_obj.times_used += 1
            discount_obj.save()
        
        return tickets


class DiscountCodeSerializer(serializers.ModelSerializer):
    """Serializer para códigos de descuento"""
    event_title = serializers.CharField(source='event.title', read_only=True)
    is_valid = serializers.ReadOnlyField()
    remaining_uses = serializers.SerializerMethodField()
    
    class Meta:
        model = DiscountCode
        fields = [
            'id', 'code', 'description', 'discount_type',
            'discount_value', 'event', 'event_title',
            'applicable_ticket_types', 'max_uses', 'times_used',
            'remaining_uses', 'max_uses_per_user', 'min_purchase_amount',
            'valid_from', 'valid_until', 'is_active', 'is_valid',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['times_used', 'created_at', 'updated_at']
    
    def get_remaining_uses(self, obj):
        """Usos restantes del código"""
        if obj.max_uses:
            return max(0, obj.max_uses - obj.times_used)
        return None
    
    def validate_code(self, value):
        """Validar código único"""
        if self.instance is None:  # Solo en creación
            if DiscountCode.objects.filter(code=value).exists():
                raise serializers.ValidationError("Este código ya existe")
        return value.upper()
    
    def validate(self, data):
        """Validaciones del código de descuento"""
        if 'valid_from' in data and 'valid_until' in data:
            if data['valid_from'] >= data['valid_until']:
                raise serializers.ValidationError(
                    "La fecha de inicio debe ser anterior a la fecha de fin"
                )
        
        if data.get('discount_type') == 'percentage':
            if data.get('discount_value', 0) > 100:
                raise serializers.ValidationError(
                    "El descuento porcentual no puede ser mayor a 100%"
                )
        
        return data


class TicketValidationSerializer(serializers.Serializer):
    """Serializer para validar tickets en el check-in"""
    ticket_code = serializers.UUIDField()
    
    def validate_ticket_code(self, value):
        """Validar que el ticket existe y es válido"""
        try:
            ticket = Ticket.objects.get(ticket_code=value)
            
            if ticket.status == 'cancelled':
                raise serializers.ValidationError("Este ticket ha sido cancelado")
            
            if ticket.status == 'used':
                raise serializers.ValidationError(
                    f"Este ticket ya fue usado el {ticket.used_at.strftime('%Y-%m-%d %H:%M')}"
                )
            
            if not ticket.is_active:
                raise serializers.ValidationError("Este ticket no está activo")
            
            # Verificar que el evento es hoy o futuro
            event = ticket.ticket_type.event
            if event.end_date < timezone.now():
                raise serializers.ValidationError("Este evento ya finalizó")
            
        except Ticket.DoesNotExist:
            raise serializers.ValidationError("Ticket no encontrado")
        
        return value