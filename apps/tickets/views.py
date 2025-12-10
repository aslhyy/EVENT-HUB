from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings

from .models import TicketType, Ticket, DiscountCode
from .serializers import (
    TicketTypeSerializer, TicketListSerializer, TicketDetailSerializer,
    TicketPurchaseSerializer, DiscountCodeSerializer, TicketValidationSerializer
)
from .filters import TicketTypeFilter, TicketFilter
from config.permissions import IsEventStaffOrReadOnly, IsTicketOwner


class TicketTypeViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar tipos de tickets
    
    list: Listar tipos de tickets disponibles
    retrieve: Obtener detalle de un tipo de ticket
    create: Crear nuevo tipo de ticket (solo organizador)
    update: Actualizar tipo de ticket (solo organizador)
    destroy: Eliminar tipo de ticket (solo organizador)
    """
    queryset = TicketType.objects.filter(is_active=True).select_related('event')
    serializer_class = TicketTypeSerializer
    permission_classes = [IsEventStaffOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = TicketTypeFilter
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'sale_start', 'display_order']
    ordering = ['display_order', 'price']
    
    @action(detail=False, methods=['get'])
    def available(self, request):
        """
        Endpoint personalizado: Tipos de tickets disponibles para la venta
        GET /api/ticket-types/available/
        """
        now = timezone.now()
        tickets = self.get_queryset().filter(
            is_active=True,
            sale_start__lte=now,
            sale_end__gte=now
        ).exclude(
            quantity_sold__gte=models.F('quantity_available')
        )
        
        event_id = request.query_params.get('event')
        if event_id:
            tickets = tickets.filter(event_id=event_id)
        
        serializer = self.get_serializer(tickets, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def sales_stats(self, request, pk=None):
        """
        Endpoint personalizado: Estadísticas de ventas de un tipo de ticket
        GET /api/ticket-types/{id}/sales_stats/
        """
        ticket_type = self.get_object()
        
        total_tickets = Ticket.objects.filter(
            ticket_type=ticket_type,
            status__in=['paid', 'confirmed', 'used']
        )
        
        stats = {
            'total_sold': ticket_type.quantity_sold,
            'total_revenue': sum(t.final_price for t in total_tickets),
            'quantity_remaining': ticket_type.quantity_remaining,
            'is_sold_out': ticket_type.is_sold_out,
            'average_price': (
                sum(t.final_price for t in total_tickets) / len(total_tickets)
                if total_tickets else 0
            ),
            'sales_by_status': {
                'paid': total_tickets.filter(status='paid').count(),
                'confirmed': total_tickets.filter(status='confirmed').count(),
                'used': total_tickets.filter(status='used').count(),
            }
        }
        
        return Response(stats)


class TicketViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar tickets
    
    list: Listar mis tickets
    retrieve: Obtener detalle de un ticket
    create: Comprar tickets
    update: Actualizar ticket (solo organizador)
    """
    queryset = Ticket.objects.all().select_related(
        'ticket_type', 'ticket_type__event', 'buyer', 'attendee'
    )
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = TicketFilter
    search_fields = ['ticket_code', 'transaction_id']
    ordering_fields = ['purchase_date', 'final_price']
    ordering = ['-purchase_date']
    
    def get_serializer_class(self):
        """Usar serializer diferente según la acción"""
        if self.action == 'list':
            return TicketListSerializer
        elif self.action == 'purchase':
            return TicketPurchaseSerializer
        elif self.action == 'validate':
            return TicketValidationSerializer
        return TicketDetailSerializer
    
    def get_queryset(self):
        """Personalizar queryset según el usuario"""
        user = self.request.user
        
        if user.is_staff:
            return self.queryset
        
        # Los usuarios ven solo sus tickets
        return self.queryset.filter(buyer=user)
    
    @action(detail=False, methods=['post'])
    @transaction.atomic
    def purchase(self, request):
        """
        Endpoint personalizado: Comprar tickets
        POST /api/tickets/purchase/
        Body: {
            "ticket_type_id": 1,
            "quantity": 2,
            "discount_code": "EARLYBIRD",
            "payment_method": "credit_card"
        }
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        tickets = serializer.save()
        
        # Enviar email de confirmación
        self._send_purchase_confirmation(request.user, tickets)
        
        return Response(
            {
                'success': True,
                'message': f'{len(tickets)} ticket(s) comprado(s) exitosamente',
                'tickets': TicketDetailSerializer(tickets, many=True).data
            },
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['get'])
    def my_tickets(self, request):
        """
        Endpoint personalizado: Mis tickets comprados
        GET /api/tickets/my_tickets/
        """
        tickets = self.get_queryset()
        
        # Filtros opcionales
        event_id = request.query_params.get('event')
        if event_id:
            tickets = tickets.filter(ticket_type__event_id=event_id)
        
        ticket_status = request.query_params.get('status')
        if ticket_status:
            tickets = tickets.filter(status=ticket_status)
        
        serializer = TicketListSerializer(tickets, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Endpoint personalizado: Cancelar ticket
        POST /api/tickets/{id}/cancel/
        Body: {"reason": "No puedo asistir"}
        """
        ticket = self.get_object()
        
        # Verificar que el usuario es el comprador
        if ticket.buyer != request.user and not request.user.is_staff:
            return Response(
                {'error': 'No tiene permisos para cancelar este ticket'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Verificar que no esté ya cancelado o usado
        if ticket.status in ['cancelled', 'used']:
            return Response(
                {'error': f'Este ticket ya está {ticket.get_status_display()}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reason = request.data.get('reason', '')
        
        with transaction.atomic():
            ticket.status = 'cancelled'
            ticket.cancelled_at = timezone.now()
            ticket.cancellation_reason = reason
            ticket.save()
            
            # Devolver ticket al inventario
            ticket_type = ticket.ticket_type
            ticket_type.quantity_sold -= 1
            ticket_type.save()
        
        return Response({
            'success': True,
            'message': 'Ticket cancelado exitosamente'
        })
    
    @action(detail=False, methods=['post'])
    def validate(self, request):
        """
        Endpoint personalizado: Validar ticket para check-in
        POST /api/tickets/validate/
        Body: {"ticket_code": "uuid-here"}
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        ticket_code = serializer.validated_data['ticket_code']
        ticket = Ticket.objects.get(ticket_code=ticket_code)
        
        return Response({
            'valid': True,
            'ticket': TicketDetailSerializer(ticket).data
        })
    
    @action(detail=True, methods=['post'])
    @transaction.atomic
    def mark_as_used(self, request, pk=None):
        """
        Endpoint personalizado: Marcar ticket como usado
        POST /api/tickets/{id}/mark_as_used/
        """
        ticket = self.get_object()
        
        # Verificar permisos (organizador o staff)
        event = ticket.ticket_type.event
        if event.organizer != request.user and not request.user.is_staff:
            return Response(
                {'error': 'No tiene permisos para esta acción'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if ticket.status == 'used':
            return Response(
                {'error': 'Este ticket ya fue usado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        ticket.status = 'used'
        ticket.used_at = timezone.now()
        ticket.save()
        
        return Response({
            'success': True,
            'message': 'Ticket marcado como usado',
            'used_at': ticket.used_at
        })
    
    def _send_purchase_confirmation(self, user, tickets):
        """Enviar email de confirmación de compra"""
        if not tickets:
            return
        
        ticket = tickets[0]
        event = ticket.ticket_type.event
        
        subject = f'Confirmación de compra - {event.title}'
        message = f"""
        Hola {user.username},
        
        Tu compra ha sido confirmada exitosamente.
        
        Evento: {event.title}
        Cantidad de tickets: {len(tickets)}
        Total pagado: ${sum(t.final_price for t in tickets):,.2f}
        
        Tus códigos de ticket:
        {chr(10).join([f'- {t.ticket_code}' for t in tickets])}
        
        ¡Nos vemos en el evento!
        """
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=True,
            )
        except Exception as e:
            # Log error pero no fallar la compra
            print(f"Error enviando email: {e}")


class DiscountCodeViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar códigos de descuento
    
    list: Listar códigos de descuento
    retrieve: Obtener detalle de un código
    create: Crear nuevo código (solo organizador)
    update: Actualizar código (solo organizador)
    destroy: Eliminar código (solo organizador)
    """
    queryset = DiscountCode.objects.filter(is_active=True)
    serializer_class = DiscountCodeSerializer
    permission_classes = [IsEventStaffOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['code', 'description']
    ordering_fields = ['valid_from', 'discount_value', 'times_used']
    ordering = ['-created_at']
    
    def get_permissions(self):
        """Allow unauthenticated access to verify action"""
        if self.action == 'verify':
            from rest_framework.permissions import AllowAny
            return [AllowAny()]
        return super().get_permissions()
    
    @action(detail=False, methods=['post'])
    def verify(self, request):

        """
        Endpoint personalizado: Verificar validez de un código de descuento
        POST /api/discount-codes/verify/
        Body: {"code": "EARLYBIRD", "ticket_type_id": 1}
        """
        code = request.data.get('code', '').upper()
        ticket_type_id = request.data.get('ticket_type_id')
        
        if not code:
            return Response(
                {'valid': False, 'error': 'Código no proporcionado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            discount = DiscountCode.objects.get(code=code, is_active=True)
            
            if not discount.is_valid:
                return Response({
                    'valid': False,
                    'error': 'Código no válido o expirado'
                })
            
            # Verificar si aplica para el ticket type
            if ticket_type_id and discount.applicable_ticket_types.exists():
                from .models import TicketType
                ticket_type = TicketType.objects.get(id=ticket_type_id)
                
                if not discount.applicable_ticket_types.filter(id=ticket_type_id).exists():
                    return Response({
                        'valid': False,
                        'error': 'Este código no aplica para este tipo de ticket'
                    })
            
            return Response({
                'valid': True,
                'discount': DiscountCodeSerializer(discount).data
            })
            
        except DiscountCode.DoesNotExist:
            return Response({
                'valid': False,
                'error': 'Código no encontrado'
            })
    
    @action(detail=True, methods=['get'])
    def usage_stats(self, request, pk=None):
        """
        Endpoint personalizado: Estadísticas de uso del código
        GET /api/discount-codes/{id}/usage_stats/
        """
        discount = self.get_object()
        
        stats = {
            'code': discount.code,
            'times_used': discount.times_used,
            'max_uses': discount.max_uses,
            'remaining_uses': (
                discount.max_uses - discount.times_used
                if discount.max_uses else None
            ),
            'is_valid': discount.is_valid,
        }
        
        return Response(stats)