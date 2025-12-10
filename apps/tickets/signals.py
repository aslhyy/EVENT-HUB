"""
Signals para enviar emails automáticamente
Ubicación: apps/tickets/signals.py
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Ticket
from config.utils.email_utils import EmailService
import logging

logger = logging.getLogger('apps')


@receiver(post_save, sender=Ticket)
def send_ticket_confirmation_email(sender, instance, created, **kwargs):
    """
    Envía email de confirmación cuando se crea un ticket
    """
    if created and instance.status == 'confirmed':
        try:
            EmailService.send_ticket_confirmation(instance)
            logger.info(f"Email de confirmación enviado para ticket {instance.id}")
        except Exception as e:
            logger.error(f"Error enviando email de ticket {instance.id}: {str(e)}")