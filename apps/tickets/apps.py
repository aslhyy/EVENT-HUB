from django.apps import AppConfig


class TicketsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.tickets'
    verbose_name = 'Tickets'
    
    def ready(self):
        """Importar signals cuando la app esté lista"""
        import apps.tickets.signals