from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.events.models import Event
import uuid


class TicketType(models.Model):
    """Tipos de tickets para eventos (VIP, General, Early Bird, etc.)"""
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='ticket_types',
        verbose_name="Evento"
    )
    name = models.CharField(max_length=100, verbose_name="Nombre del ticket")
    description = models.TextField(blank=True, verbose_name="Descripción")
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Precio"
    )
    quantity_available = models.PositiveIntegerField(
        verbose_name="Cantidad disponible",
        help_text="Total de tickets de este tipo"
    )
    quantity_sold = models.PositiveIntegerField(
        default=0,
        verbose_name="Cantidad vendida"
    )
    max_per_order = models.PositiveIntegerField(
        default=10,
        validators=[MinValueValidator(1)],
        verbose_name="Máximo por orden",
        help_text="Máximo de tickets que se pueden comprar en una sola orden"
    )
    
    # Configuración de disponibilidad
    sale_start = models.DateTimeField(verbose_name="Inicio de ventas")
    sale_end = models.DateTimeField(verbose_name="Fin de ventas")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    
    # Beneficios incluidos
    includes_food = models.BooleanField(default=False, verbose_name="Incluye comida")
    includes_drink = models.BooleanField(default=False, verbose_name="Incluye bebida")
    includes_parking = models.BooleanField(default=False, verbose_name="Incluye parking")
    includes_merchandise = models.BooleanField(default=False, verbose_name="Incluye merchandising")
    benefits_description = models.TextField(
        blank=True,
        verbose_name="Descripción de beneficios"
    )
    
    # Metadata
    display_order = models.PositiveIntegerField(
        default=0,
        verbose_name="Orden de visualización"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ticket_types'
        verbose_name = 'Tipo de Ticket'
        verbose_name_plural = 'Tipos de Tickets'
        ordering = ['event', 'display_order', 'price']
        indexes = [
            models.Index(fields=['event', 'is_active']),
        ]

    def __str__(self):
        return f"{self.event.title} - {self.name}"

    @property
    def quantity_remaining(self):
        """Cantidad de tickets disponibles"""
        return max(0, self.quantity_available - self.quantity_sold)

    @property
    def is_sold_out(self):
        """Verifica si está agotado"""
        return self.quantity_remaining == 0

    @property
    def is_on_sale(self):
        """Verifica si está en período de venta"""
        from django.utils import timezone
        now = timezone.now()
        return (
            self.is_active and 
            self.sale_start <= now <= self.sale_end and 
            not self.is_sold_out
        )


class Ticket(models.Model):
    """Tickets individuales comprados por usuarios"""
    STATUS_CHOICES = [
        ('reserved', 'Reservado'),
        ('paid', 'Pagado'),
        ('confirmed', 'Confirmado'),
        ('used', 'Usado'),
        ('cancelled', 'Cancelado'),
        ('refunded', 'Reembolsado'),
    ]

    # Identificación única
    ticket_code = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name="Código de ticket"
    )
    qr_code = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Código QR"
    )
    
    # Relaciones
    ticket_type = models.ForeignKey(
        TicketType,
        on_delete=models.PROTECT,
        related_name='tickets',
        verbose_name="Tipo de ticket"
    )
    buyer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='purchased_tickets',
        verbose_name="Comprador"
    )
    attendee = models.OneToOneField(
        'attendees.Attendee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ticket',
        verbose_name="Asistente"
    )
    
    # Información de compra
    purchase_date = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de compra")
    payment_method = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Método de pago"
    )
    transaction_id = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="ID de transacción"
    )
    
    # Precios
    original_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Precio original"
    )
    discount_applied = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Descuento aplicado"
    )
    final_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Precio final"
    )
    
    # Estado y uso
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='reserved',
        verbose_name="Estado"
    )
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    used_at = models.DateTimeField(null=True, blank=True, verbose_name="Usado en")
    cancelled_at = models.DateTimeField(null=True, blank=True, verbose_name="Cancelado en")
    cancellation_reason = models.TextField(blank=True, verbose_name="Razón de cancelación")
    
    # Metadata
    notes = models.TextField(blank=True, verbose_name="Notas")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tickets'
        verbose_name = 'Ticket'
        verbose_name_plural = 'Tickets'
        ordering = ['-purchase_date']
        indexes = [
            models.Index(fields=['ticket_code']),
            models.Index(fields=['buyer', 'status']),
            models.Index(fields=['ticket_type', 'status']),
        ]

    def __str__(self):
        return f"Ticket {self.ticket_code} - {self.ticket_type.name}"

    def save(self, *args, **kwargs):
        # Calcular precio final si no está definido
        if not self.final_price:
            self.final_price = self.original_price - self.discount_applied
        
        # Generar código QR si no existe
        if not self.qr_code:
            self.qr_code = f"QR-{self.ticket_code}"
        
        super().save(*args, **kwargs)


class DiscountCode(models.Model):
    """Códigos de descuento para tickets"""
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Porcentaje'),
        ('fixed', 'Monto fijo'),
    ]

    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Código"
    )
    description = models.CharField(max_length=200, blank=True, verbose_name="Descripción")
    
    # Tipo de descuento
    discount_type = models.CharField(
        max_length=20,
        choices=DISCOUNT_TYPE_CHOICES,
        default='percentage',
        verbose_name="Tipo de descuento"
    )
    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Valor del descuento"
    )
    
    # Aplicabilidad
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='discount_codes',
        null=True,
        blank=True,
        verbose_name="Evento específico"
    )
    applicable_ticket_types = models.ManyToManyField(
        TicketType,
        blank=True,
        related_name='discount_codes',
        verbose_name="Tipos de ticket aplicables"
    )
    
    # Límites
    max_uses = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Usos máximos"
    )
    times_used = models.PositiveIntegerField(default=0, verbose_name="Veces usado")
    max_uses_per_user = models.PositiveIntegerField(
        default=1,
        verbose_name="Usos máximos por usuario"
    )
    min_purchase_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Compra mínima requerida"
    )
    
    # Vigencia
    valid_from = models.DateTimeField(verbose_name="Válido desde")
    valid_until = models.DateTimeField(verbose_name="Válido hasta")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    
    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_discount_codes',
        verbose_name="Creado por"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'discount_codes'
        verbose_name = 'Código de Descuento'
        verbose_name_plural = 'Códigos de Descuento'
        ordering = ['-created_at']

    def __str__(self):
        return self.code

    @property
    def is_valid(self):
        """Verifica si el código es válido"""
        from django.utils import timezone
        now = timezone.now()
        
        if not self.is_active:
            return False
        if not (self.valid_from <= now <= self.valid_until):
            return False
        if self.max_uses and self.times_used >= self.max_uses:
            return False
        
        return True