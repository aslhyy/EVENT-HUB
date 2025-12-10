"""
Sistema de envío de emails para EventHub
Ubicación: config/utils/email_utils.py
"""

from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
import logging

logger = logging.getLogger('apps')


class EmailService:
    """Servicio para enviar emails"""
    
    @staticmethod
    def send_email(subject, message, recipient_list, html_message=None):
        """
        Envía un email simple
        
        Args:
            subject: Asunto del email
            message: Mensaje en texto plano
            recipient_list: Lista de destinatarios
            html_message: Mensaje HTML opcional
        """
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipient_list,
                html_message=html_message,
                fail_silently=False,
            )
            logger.info(f"Email enviado a {recipient_list}")
            return True
        except Exception as e:
            logger.error(f"Error enviando email: {str(e)}")
            return False
    
    @staticmethod
    def send_welcome_email(user):
        """Envía email de bienvenida"""
        subject = '¡Bienvenido a EventHub! 🎉'
        message = f"""
        Hola {user.first_name or user.username},
        
        ¡Bienvenido a EventHub!
        
        Tu cuenta ha sido creada exitosamente. Ahora puedes:
        - Explorar eventos increíbles
        - Comprar tickets
        - Gestionar tus asistencias
        - Y mucho más!
        
        ¡Gracias por unirte a nosotros!
        
        Equipo EventHub
        """
        
        html_message = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h1 style="color: #6366f1;">¡Bienvenido a EventHub! 🎉</h1>
                    <p>Hola <strong>{user.first_name or user.username}</strong>,</p>
                    <p>¡Tu cuenta ha sido creada exitosamente!</p>
                    
                    <div style="background: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="margin-top: 0;">Ahora puedes:</h3>
                        <ul>
                            <li>✨ Explorar eventos increíbles</li>
                            <li>🎫 Comprar tickets</li>
                            <li>📋 Gestionar tus asistencias</li>
                            <li>🎉 Y mucho más!</li>
                        </ul>
                    </div>
                    
                    <p>¡Gracias por unirte a nosotros!</p>
                    <p style="color: #6366f1;"><strong>Equipo EventHub</strong></p>
                </div>
            </body>
        </html>
        """
        
        return EmailService.send_email(
            subject=subject,
            message=message,
            recipient_list=[user.email],
            html_message=html_message
        )
    
    @staticmethod
    def send_ticket_confirmation(ticket):
        """Envía confirmación de compra de ticket"""
        event = ticket.ticket_type.event
        user = ticket.user
        
        subject = f'Confirmación de Ticket - {event.title}'
        message = f"""
        Hola {user.first_name or user.username},
        
        ¡Tu ticket ha sido confirmado!
        
        Detalles del Evento:
        - Evento: {event.title}
        - Fecha: {event.start_date.strftime('%d/%m/%Y %H:%M')}
        - Ubicación: {event.venue.name}
        - Tipo de Ticket: {ticket.ticket_type.name}
        - Precio: ${ticket.final_price}
        - Código QR: {ticket.qr_code}
        
        Presenta este código en el evento para tu ingreso.
        
        ¡Nos vemos en el evento!
        
        Equipo EventHub
        """
        
        html_message = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h1 style="color: #6366f1;">¡Ticket Confirmado! 🎫</h1>
                    <p>Hola <strong>{user.first_name or user.username}</strong>,</p>
                    <p>¡Tu ticket ha sido confirmado exitosamente!</p>
                    
                    <div style="background: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="margin-top: 0; color: #6366f1;">Detalles del Evento</h3>
                        <p><strong>🎉 Evento:</strong> {event.title}</p>
                        <p><strong>📅 Fecha:</strong> {event.start_date.strftime('%d de %B, %Y a las %H:%M')}</p>
                        <p><strong>📍 Ubicación:</strong> {event.venue.name}, {event.venue.address}</p>
                        <p><strong>🎫 Tipo de Ticket:</strong> {ticket.ticket_type.name}</p>
                        <p><strong>💰 Precio:</strong> ${ticket.final_price}</p>
                        <p><strong>🔑 Código QR:</strong> <code style="background: #e5e7eb; padding: 4px 8px; border-radius: 4px;">{ticket.qr_code}</code></p>
                    </div>
                    
                    <div style="background: #dbeafe; border-left: 4px solid #3b82f6; padding: 15px; margin: 20px 0;">
                        <p style="margin: 0;"><strong>💡 Importante:</strong> Presenta este código en el evento para tu ingreso.</p>
                    </div>
                    
                    <p>¡Nos vemos en el evento!</p>
                    <p style="color: #6366f1;"><strong>Equipo EventHub</strong></p>
                </div>
            </body>
        </html>
        """
        
        return EmailService.send_email(
            subject=subject,
            message=message,
            recipient_list=[user.email],
            html_message=html_message
        )
    
    @staticmethod
    def send_event_reminder(event, attendees):
        """Envía recordatorio de evento próximo"""
        subject = f'Recordatorio: {event.title} es mañana!'
        
        for attendee in attendees:
            message = f"""
            Hola {attendee.user.first_name or attendee.user.username},
            
            ¡Tu evento es mañana!
            
            Evento: {event.title}
            Fecha: {event.start_date.strftime('%d/%m/%Y %H:%M')}
            Ubicación: {event.venue.name}
            Dirección: {event.venue.address}
            
            No olvides llegar 15 minutos antes.
            
            ¡Te esperamos!
            
            Equipo EventHub
            """
            
            html_message = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h1 style="color: #ec4899;">¡Tu evento es mañana! ⏰</h1>
                        <p>Hola <strong>{attendee.user.first_name or attendee.user.username}</strong>,</p>
                        
                        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
                            <h2 style="margin-top: 0; color: white;">{event.title}</h2>
                            <p><strong>📅 Fecha:</strong> {event.start_date.strftime('%d de %B, %Y')}</p>
                            <p><strong>🕐 Hora:</strong> {event.start_date.strftime('%H:%M')}</p>
                            <p><strong>📍 Ubicación:</strong> {event.venue.name}</p>
                            <p><strong>🗺️ Dirección:</strong> {event.venue.address}</p>
                        </div>
                        
                        <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin: 20px 0;">
                            <p style="margin: 0;"><strong>💡 Recuerda:</strong> Llegar 15 minutos antes para el check-in.</p>
                        </div>
                        
                        <p>¡Te esperamos!</p>
                        <p style="color: #ec4899;"><strong>Equipo EventHub</strong></p>
                    </div>
                </body>
            </html>
            """
            
            EmailService.send_email(
                subject=subject,
                message=message,
                recipient_list=[attendee.user.email],
                html_message=html_message
            )
    
    @staticmethod
    def send_event_cancellation(event, attendees):
        """Envía notificación de evento cancelado"""
        subject = f'Evento Cancelado: {event.title}'
        
        for attendee in attendees:
            message = f"""
            Hola {attendee.user.first_name or attendee.user.username},
            
            Lamentablemente, el evento {event.title} ha sido cancelado.
            
            Se procesará el reembolso completo en los próximos 5-7 días hábiles.
            
            Disculpa las molestias.
            
            Equipo EventHub
            """
            
            html_message = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h1 style="color: #ef4444;">Evento Cancelado</h1>
                        <p>Hola <strong>{attendee.user.first_name or attendee.user.username}</strong>,</p>
                        <p>Lamentablemente, el evento <strong>{event.title}</strong> ha sido cancelado.</p>
                        
                        <div style="background: #fee2e2; border-left: 4px solid #ef4444; padding: 15px; margin: 20px 0;">
                            <p style="margin: 0;"><strong>💰 Reembolso:</strong> Se procesará el reembolso completo en los próximos 5-7 días hábiles.</p>
                        </div>
                        
                        <p>Disculpa las molestias.</p>
                        <p style="color: #6366f1;"><strong>Equipo EventHub</strong></p>
                    </div>
                </body>
            </html>
            """
            
            EmailService.send_email(
                subject=subject,
                message=message,
                recipient_list=[attendee.user.email],
                html_message=html_message
            )