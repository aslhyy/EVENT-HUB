from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from apps.events.models import Event


class Attendee(models.Model):
    """Asistentes registrados a eventos"""
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('confirmed', 'Confirmado'),
        ('checked_in', 'Ingresado'),
        ('cancelled', 'Cancelado'),
        ('no_show', 'No asistió'),
    ]

    # Relaciones
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='attendee_profiles',
        verbose_name="Usuario"
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='attendees',
        verbose_name="Evento"
    )
    
    # Información personal
    first_name = models.CharField(max_length=100, verbose_name="Nombre")
    last_name = models.CharField(max_length=100, verbose_name="Apellido")
    email = models.EmailField(verbose_name="Email")
    phone_validator = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="El número debe estar en formato: '+999999999'. Hasta 15 dígitos."
    )
    phone = models.CharField(
        validators=[phone_validator],
        max_length=17,
        verbose_name="Teléfono"
    )
    
    # Información adicional
    company = models.CharField(max_length=200, blank=True, verbose_name="Empresa")
    job_title = models.CharField(max_length=150, blank=True, verbose_name="Cargo")
    dietary_restrictions = models.TextField(
        blank=True,
        verbose_name="Restricciones alimentarias"
    )
    special_requirements = models.TextField(
        blank=True,
        verbose_name="Requerimientos especiales"
    )
    
    # Estado de asistencia
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Estado"
    )
    registration_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de registro"
    )
    confirmation_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de confirmación"
    )
    
    # Check-in information
    checked_in_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de ingreso"
    )
    checked_in_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='checked_in_attendees',
        verbose_name="Registrado por"
    )
    
    # Preferencias de comunicación
    receive_reminders = models.BooleanField(
        default=True,
        verbose_name="Recibir recordatorios"
    )
    receive_updates = models.BooleanField(
        default=True,
        verbose_name="Recibir actualizaciones"
    )
    
    # Metadata
    notes = models.TextField(blank=True, verbose_name="Notas")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'attendees'
        verbose_name = 'Asistente'
        verbose_name_plural = 'Asistentes'
        ordering = ['-registration_date']
        unique_together = ['user', 'event']
        indexes = [
            models.Index(fields=['event', 'status']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.event.title}"

    @property
    def full_name(self):
        """Nombre completo del asistente"""
        return f"{self.first_name} {self.last_name}"


class CheckInLog(models.Model):
    """Registro de check-ins en eventos"""
    attendee = models.ForeignKey(
        Attendee,
        on_delete=models.CASCADE,
        related_name='checkin_logs',
        verbose_name="Asistente"
    )
    checked_in_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='performed_checkins',
        verbose_name="Registrado por"
    )
    checked_in_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha y hora")
    location = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Ubicación",
        help_text="Ej: Puerta A, Registro Principal"
    )
    device_info = models.CharField(
        max_length=300,
        blank=True,
        verbose_name="Información del dispositivo"
    )
    notes = models.TextField(blank=True, verbose_name="Notas")

    class Meta:
        db_table = 'checkin_logs'
        verbose_name = 'Registro de Check-in'
        verbose_name_plural = 'Registros de Check-in'
        ordering = ['-checked_in_at']

    def __str__(self):
        return f"Check-in: {self.attendee.full_name} - {self.checked_in_at}"


class Survey(models.Model):
    """Encuestas para eventos"""
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='surveys',
        verbose_name="Evento"
    )
    title = models.CharField(max_length=200, verbose_name="Título")
    description = models.TextField(blank=True, verbose_name="Descripción")
    
    # Configuración
    is_active = models.BooleanField(default=True, verbose_name="Activa")
    is_anonymous = models.BooleanField(default=False, verbose_name="Anónima")
    allow_multiple_responses = models.BooleanField(
        default=False,
        verbose_name="Permitir múltiples respuestas"
    )
    
    # Disponibilidad
    available_from = models.DateTimeField(verbose_name="Disponible desde")
    available_until = models.DateTimeField(verbose_name="Disponible hasta")
    
    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_surveys',
        verbose_name="Creada por"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'surveys'
        verbose_name = 'Encuesta'
        verbose_name_plural = 'Encuestas'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.event.title}"

    @property
    def is_available(self):
        """Verifica si la encuesta está disponible"""
        from django.utils import timezone
        now = timezone.now()
        return (
            self.is_active and
            self.available_from <= now <= self.available_until
        )


class SurveyQuestion(models.Model):
    """Preguntas de encuestas"""
    QUESTION_TYPES = [
        ('text', 'Texto libre'),
        ('rating', 'Calificación (1-5)'),
        ('multiple_choice', 'Opción múltiple'),
        ('checkbox', 'Casillas de verificación'),
        ('yes_no', 'Sí/No'),
    ]

    survey = models.ForeignKey(
        Survey,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name="Encuesta"
    )
    question_text = models.TextField(verbose_name="Pregunta")
    question_type = models.CharField(
        max_length=20,
        choices=QUESTION_TYPES,
        verbose_name="Tipo de pregunta"
    )
    options = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Opciones",
        help_text="Para preguntas de opción múltiple o checkboxes"
    )
    is_required = models.BooleanField(default=False, verbose_name="Obligatoria")
    order = models.PositiveIntegerField(default=0, verbose_name="Orden")

    class Meta:
        db_table = 'survey_questions'
        verbose_name = 'Pregunta de Encuesta'
        verbose_name_plural = 'Preguntas de Encuesta'
        ordering = ['survey', 'order']

    def __str__(self):
        return f"{self.survey.title} - Q{self.order}"


class SurveyResponse(models.Model):
    """Respuestas a encuestas"""
    survey = models.ForeignKey(
        Survey,
        on_delete=models.CASCADE,
        related_name='responses',
        verbose_name="Encuesta"
    )
    attendee = models.ForeignKey(
        Attendee,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='survey_responses',
        verbose_name="Asistente"
    )
    question = models.ForeignKey(
        SurveyQuestion,
        on_delete=models.CASCADE,
        related_name='responses',
        verbose_name="Pregunta"
    )
    answer = models.TextField(verbose_name="Respuesta")
    submitted_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de envío")

    class Meta:
        db_table = 'survey_responses'
        verbose_name = 'Respuesta de Encuesta'
        verbose_name_plural = 'Respuestas de Encuestas'
        ordering = ['-submitted_at']

    def __str__(self):
        return f"Respuesta: {self.survey.title} - {self.submitted_at}"