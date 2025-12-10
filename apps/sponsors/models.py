from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, URLValidator
from apps.events.models import Event


class SponsorTier(models.Model):
    """Niveles de patrocinio (Platinum, Gold, Silver, Bronze)"""
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nombre del nivel"
    )
    description = models.TextField(blank=True, verbose_name="Descripción")
    
    # Configuración financiera
    min_contribution = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Contribución mínima"
    )
    max_contribution = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Contribución máxima"
    )
    
    # Beneficios
    benefits = models.TextField(
        verbose_name="Beneficios incluidos",
        help_text="Lista de beneficios separados por saltos de línea"
    )
    priority_level = models.PositiveIntegerField(
        default=0,
        verbose_name="Nivel de prioridad",
        help_text="Mayor número = mayor prioridad"
    )
    
    # Visibilidad
    logo_size = models.CharField(
        max_length=50,
        default='medium',
        verbose_name="Tamaño del logo",
        help_text="small, medium, large, xlarge"
    )
    homepage_featured = models.BooleanField(
        default=False,
        verbose_name="Destacado en página principal"
    )
    speaking_opportunity = models.BooleanField(
        default=False,
        verbose_name="Oportunidad de hablar"
    )
    booth_space = models.BooleanField(
        default=False,
        verbose_name="Espacio para stand"
    )
    
    # Entradas incluidas
    complimentary_tickets = models.PositiveIntegerField(
        default=0,
        verbose_name="Tickets de cortesía"
    )
    vip_tickets = models.PositiveIntegerField(
        default=0,
        verbose_name="Tickets VIP"
    )
    
    # Metadata
    color = models.CharField(
        max_length=7,
        default='#CCCCCC',
        verbose_name="Color representativo",
        help_text="Código hexadecimal, ej: #FFD700"
    )
    icon = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Icono"
    )
    display_order = models.PositiveIntegerField(
        default=0,
        verbose_name="Orden de visualización"
    )
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'sponsor_tiers'
        verbose_name = 'Nivel de Patrocinio'
        verbose_name_plural = 'Niveles de Patrocinio'
        ordering = ['-priority_level', 'display_order']

    def __str__(self):
        return self.name


class Sponsor(models.Model):
    """Patrocinadores de eventos"""
    STATUS_CHOICES = [
        ('prospective', 'Prospecto'),
        ('negotiating', 'En negociación'),
        ('confirmed', 'Confirmado'),
        ('active', 'Activo'),
        ('completed', 'Completado'),
        ('cancelled', 'Cancelado'),
    ]

    # Información básica
    name = models.CharField(max_length=200, verbose_name="Nombre de la empresa")
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(verbose_name="Descripción")
    industry = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Industria"
    )
    
    # Contacto
    contact_person = models.CharField(
        max_length=200,
        verbose_name="Persona de contacto"
    )
    contact_email = models.EmailField(verbose_name="Email de contacto")
    contact_phone = models.CharField(max_length=20, verbose_name="Teléfono")
    
    # Online presence
    website = models.URLField(
        blank=True,
        validators=[URLValidator()],
        verbose_name="Sitio web"
    )
    linkedin_url = models.URLField(blank=True, verbose_name="LinkedIn")
    twitter_url = models.URLField(blank=True, verbose_name="Twitter/X")
    instagram_url = models.URLField(blank=True, verbose_name="Instagram")
    facebook_url = models.URLField(blank=True, verbose_name="Facebook")
    
    # Multimedia
    logo = models.ImageField(
        upload_to='sponsors/logos/',
        verbose_name="Logo"
    )
    banner_image = models.ImageField(
        upload_to='sponsors/banners/',
        null=True,
        blank=True,
        verbose_name="Banner"
    )
    
    # Nivel y relación
    tier = models.ForeignKey(
        SponsorTier,
        on_delete=models.PROTECT,
        related_name='sponsors',
        null=True,
        blank=True,
        verbose_name="Nivel de patrocinio"
    )
    events = models.ManyToManyField(
        Event,
        through='Sponsorship',
        related_name='sponsors',
        verbose_name="Eventos"
    )
    
    # Estado
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='prospective',
        verbose_name="Estado"
    )
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    
    # Usuario responsable
    account_manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_sponsors',
        verbose_name="Responsable de cuenta"
    )
    
    # Metadata
    notes = models.TextField(blank=True, verbose_name="Notas internas")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'sponsors'
        verbose_name = 'Patrocinador'
        verbose_name_plural = 'Patrocinadores'
        ordering = ['name']
        indexes = [
            models.Index(fields=['status', 'is_active']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Sponsorship(models.Model):
    """Relación entre patrocinadores y eventos (tabla intermedia)"""
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('partial', 'Parcial'),
        ('completed', 'Completado'),
        ('refunded', 'Reembolsado'),
    ]

    # Relaciones
    sponsor = models.ForeignKey(
        Sponsor,
        on_delete=models.CASCADE,
        related_name='sponsorships',
        verbose_name="Patrocinador"
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='sponsorships',
        verbose_name="Evento"
    )
    tier = models.ForeignKey(
        SponsorTier,
        on_delete=models.PROTECT,
        related_name='sponsorships',
        verbose_name="Nivel"
    )
    
    # Información financiera
    contribution_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Monto de contribución"
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending',
        verbose_name="Estado de pago"
    )
    amount_paid = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Monto pagado"
    )
    
    # Fechas importantes
    contract_signed_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de firma de contrato"
    )
    payment_due_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha límite de pago"
    )
    
    # Beneficios específicos
    custom_benefits = models.TextField(
        blank=True,
        verbose_name="Beneficios personalizados",
        help_text="Beneficios adicionales o personalizados"
    )
    booth_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Número de stand"
    )
    speaking_slot = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Horario para presentación"
    )
    
    # Documentos
    contract_document = models.FileField(
        upload_to='sponsors/contracts/%Y/%m/',
        null=True,
        blank=True,
        verbose_name="Documento de contrato"
    )
    
    # Estado
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    is_public = models.BooleanField(
        default=True,
        verbose_name="Visible públicamente"
    )
    
    # Metadata
    notes = models.TextField(blank=True, verbose_name="Notas")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'sponsorships'
        verbose_name = 'Patrocinio'
        verbose_name_plural = 'Patrocinios'
        unique_together = ['sponsor', 'event']
        ordering = ['-contribution_amount']
        indexes = [
            models.Index(fields=['event', 'is_public']),
        ]

    def __str__(self):
        return f"{self.sponsor.name} - {self.event.title}"

    @property
    def remaining_balance(self):
        """Calcula el saldo pendiente"""
        return self.contribution_amount - self.amount_paid

    @property
    def payment_progress_percentage(self):
        """Calcula el porcentaje de pago completado"""
        if self.contribution_amount == 0:
            return 0
        return (self.amount_paid / self.contribution_amount) * 100


class SponsorBenefit(models.Model):
    """Beneficios entregados a patrocinadores"""
    sponsorship = models.ForeignKey(
        Sponsorship,
        on_delete=models.CASCADE,
        related_name='delivered_benefits',
        verbose_name="Patrocinio"
    )
    benefit_name = models.CharField(max_length=200, verbose_name="Nombre del beneficio")
    description = models.TextField(blank=True, verbose_name="Descripción")
    
    # Estado de entrega
    is_delivered = models.BooleanField(default=False, verbose_name="Entregado")
    delivered_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de entrega"
    )
    delivered_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='delivered_benefits',
        verbose_name="Entregado por"
    )
    
    # Evidencia
    proof_document = models.FileField(
        upload_to='sponsors/benefits/%Y/%m/',
        null=True,
        blank=True,
        verbose_name="Documento de evidencia"
    )
    notes = models.TextField(blank=True, verbose_name="Notas")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'sponsor_benefits'
        verbose_name = 'Beneficio de Patrocinador'
        verbose_name_plural = 'Beneficios de Patrocinadores'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.benefit_name} - {self.sponsorship}"