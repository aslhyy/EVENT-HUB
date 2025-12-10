from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils.text import slugify


class Category(models.Model):
    """Categorías de eventos (Música, Deportes, Tecnología, etc.)"""
    name = models.CharField(max_length=100, unique=True, verbose_name="Nombre")
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True, verbose_name="Descripción")
    icon = models.CharField(max_length=50, blank=True, help_text="Icono FontAwesome")
    is_active = models.BooleanField(default=True, verbose_name="Activa")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'categories'
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Venue(models.Model):
    """Lugares/Ubicaciones donde se realizan los eventos"""
    name = models.CharField(max_length=200, verbose_name="Nombre del lugar")
    address = models.CharField(max_length=300, verbose_name="Dirección")
    city = models.CharField(max_length=100, verbose_name="Ciudad")
    state = models.CharField(max_length=100, verbose_name="Departamento/Estado")
    country = models.CharField(max_length=100, default="Colombia", verbose_name="País")
    postal_code = models.CharField(max_length=20, blank=True, verbose_name="Código postal")
    capacity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Capacidad",
        help_text="Capacidad máxima del lugar"
    )
    latitude = models.DecimalField(
        max_digits=9, 
        decimal_places=6, 
        null=True, 
        blank=True,
        verbose_name="Latitud"
    )
    longitude = models.DecimalField(
        max_digits=9, 
        decimal_places=6, 
        null=True, 
        blank=True,
        verbose_name="Longitud"
    )
    facilities = models.TextField(blank=True, verbose_name="Facilidades", help_text="Parking, WiFi, etc.")
    contact_phone = models.CharField(max_length=20, blank=True, verbose_name="Teléfono de contacto")
    contact_email = models.EmailField(blank=True, verbose_name="Email de contacto")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'venues'
        verbose_name = 'Lugar'
        verbose_name_plural = 'Lugares'
        ordering = ['name']
        indexes = [
            models.Index(fields=['city', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name} - {self.city}"


class Event(models.Model):
    """Eventos principales del sistema"""
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('published', 'Publicado'),
        ('ongoing', 'En curso'),
        ('completed', 'Completado'),
        ('cancelled', 'Cancelado'),
    ]

    title = models.CharField(max_length=300, verbose_name="Título")
    slug = models.SlugField(max_length=350, unique=True, blank=True)
    description = models.TextField(verbose_name="Descripción")
    short_description = models.CharField(
        max_length=500, 
        blank=True,
        verbose_name="Descripción corta",
        help_text="Resumen breve para listados"
    )
    
    # Relaciones
    category = models.ForeignKey(
        Category, 
        on_delete=models.PROTECT, 
        related_name='events',
        verbose_name="Categoría"
    )
    venue = models.ForeignKey(
        Venue, 
        on_delete=models.PROTECT, 
        related_name='events',
        verbose_name="Lugar"
    )
    organizer = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='organized_events',
        verbose_name="Organizador"
    )
    
    # Fechas y horarios
    start_date = models.DateTimeField(verbose_name="Fecha de inicio")
    end_date = models.DateTimeField(verbose_name="Fecha de finalización")
    registration_start = models.DateTimeField(verbose_name="Inicio de registro")
    registration_end = models.DateTimeField(verbose_name="Fin de registro")
    
    # Detalles del evento
    is_free = models.BooleanField(default=False, verbose_name="Evento gratuito")
    max_attendees = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Máximo de asistentes",
        help_text="Dejar vacío para sin límite"
    )
    
    # Multimedia
    banner_image = models.ImageField(
        upload_to='events/banners/%Y/%m/',
        null=True,
        blank=True,
        verbose_name="Imagen banner"
    )
    thumbnail_image = models.ImageField(
        upload_to='events/thumbnails/%Y/%m/',
        null=True,
        blank=True,
        verbose_name="Imagen miniatura"
    )
    
    # Estado y visibilidad
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='draft',
        verbose_name="Estado"
    )
    is_featured = models.BooleanField(default=False, verbose_name="Destacado")
    is_published = models.BooleanField(default=False, verbose_name="Publicado")
    
    # Metadata
    views_count = models.PositiveIntegerField(default=0, verbose_name="Vistas")
    tags = models.CharField(max_length=500, blank=True, verbose_name="Etiquetas", help_text="Separadas por comas")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de publicación")

    class Meta:
        db_table = 'events'
        verbose_name = 'Evento'
        verbose_name_plural = 'Eventos'
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['-start_date', 'status']),
            models.Index(fields=['category', 'is_published']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    @property
    def is_active(self):
        """Verifica si el evento está activo"""
        from django.utils import timezone
        return self.status == 'published' and self.start_date > timezone.now()

    @property
    def available_spots(self):
        """Calcula cupos disponibles"""
        if not self.max_attendees:
            return None
        registered = self.attendees.filter(status='confirmed').count()
        return max(0, self.max_attendees - registered)