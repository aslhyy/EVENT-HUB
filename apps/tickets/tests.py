from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from decimal import Decimal

from .models import TicketType, Ticket, DiscountCode
from apps.events.models import Event, Category, Venue


class TicketTypeModelTest(TestCase):
    """Tests para el modelo TicketType"""
    
    def setUp(self):
        user = User.objects.create_user(username='organizer', password='pass123')
        category = Category.objects.create(name="Música")
        venue = Venue.objects.create(
            name="Estadio", address="Calle 1", city="Bogotá",
            state="Cundinamarca", capacity=1000
        )
        
        now = timezone.now()
        
        self.event = Event.objects.create(
            title="Concierto Rock",
            description="Evento musical",
            category=category,
            venue=venue,
            organizer=user,
            start_date=now + timedelta(days=30),
            end_date=now + timedelta(days=30, hours=4),
            registration_start=now,
            registration_end=now + timedelta(days=29),
            status='published',
            is_published=True
        )
        
        self.ticket_type = TicketType.objects.create(
            event=self.event,
            name="General",
            price=Decimal('50000.00'),
            quantity_available=100,
            sale_start=now,
            sale_end=now + timedelta(days=29)
        )
    
    def test_ticket_type_creation(self):
        """Test crear tipo de ticket"""
        self.assertEqual(self.ticket_type.name, "General")
        self.assertEqual(self.ticket_type.price, Decimal('50000.00'))
        self.assertEqual(self.ticket_type.quantity_available, 100)
    
    def test_quantity_remaining(self):
        """Test cálculo de cantidad restante"""
        self.assertEqual(self.ticket_type.quantity_remaining, 100)
        
        self.ticket_type.quantity_sold = 30
        self.ticket_type.save()
        
        self.assertEqual(self.ticket_type.quantity_remaining, 70)
    
    def test_is_sold_out(self):
        """Test verificación de agotado"""
        self.assertFalse(self.ticket_type.is_sold_out)
        
        self.ticket_type.quantity_sold = 100
        self.ticket_type.save()
        
        self.assertTrue(self.ticket_type.is_sold_out)
    
    def test_is_on_sale(self):
        """Test verificación de en venta"""
        self.assertTrue(self.ticket_type.is_on_sale)


class TicketModelTest(TestCase):
    """Tests para el modelo Ticket"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='buyer', password='pass123')
        organizer = User.objects.create_user(username='organizer', password='pass123')
        category = Category.objects.create(name="Deportes")
        venue = Venue.objects.create(
            name="Estadio", address="Av 1", city="Medellín",
            state="Antioquia", capacity=500
        )
        
        now = timezone.now()
        
        event = Event.objects.create(
            title="Partido",
            description="Evento deportivo",
            category=category,
            venue=venue,
            organizer=organizer,
            start_date=now + timedelta(days=15),
            end_date=now + timedelta(days=15, hours=2),
            registration_start=now,
            registration_end=now + timedelta(days=14),
            status='published',
            is_published=True
        )
        
        self.ticket_type = TicketType.objects.create(
            event=event,
            name="VIP",
            price=Decimal('100000.00'),
            quantity_available=50,
            sale_start=now,
            sale_end=now + timedelta(days=14)
        )
        
        self.ticket = Ticket.objects.create(
            ticket_type=self.ticket_type,
            buyer=self.user,
            original_price=Decimal('100000.00'),
            final_price=Decimal('100000.00'),
            status='paid'
        )
    
    def test_ticket_creation(self):
        """Test crear ticket"""
        self.assertEqual(self.ticket.buyer, self.user)
        self.assertEqual(self.ticket.status, 'paid')
        self.assertIsNotNone(self.ticket.ticket_code)
    
    def test_qr_code_generation(self):
        """Test generación de código QR"""
        self.assertIsNotNone(self.ticket.qr_code)
        self.assertIn(str(self.ticket.ticket_code), self.ticket.qr_code)


class DiscountCodeModelTest(TestCase):
    """Tests para el modelo DiscountCode"""
    
    def setUp(self):
        user = User.objects.create_user(username='admin', password='pass123')
        category = Category.objects.create(name="Tecnología")
        venue = Venue.objects.create(
            name="Centro", address="Calle 1", city="Cali",
            state="Valle", capacity=300
        )
        
        now = timezone.now()
        
        self.event = Event.objects.create(
            title="Tech Summit",
            description="Evento tech",
            category=category,
            venue=venue,
            organizer=user,
            start_date=now + timedelta(days=20),
            end_date=now + timedelta(days=20, hours=8),
            registration_start=now,
            registration_end=now + timedelta(days=19),
            status='published',
            is_published=True
        )
        
        self.discount = DiscountCode.objects.create(
            code="EARLYBIRD",
            discount_type="percentage",
            discount_value=Decimal('20.00'),
            event=self.event,
            max_uses=100,
            valid_from=now,
            valid_until=now + timedelta(days=10),
            is_active=True
        )
    
    def test_discount_creation(self):
        """Test crear código de descuento"""
        self.assertEqual(self.discount.code, "EARLYBIRD")
        self.assertEqual(self.discount.discount_value, Decimal('20.00'))
    
    def test_is_valid(self):
        """Test validación de código"""
        self.assertTrue(self.discount.is_valid)
        
        # Marcar como usado completamente
        self.discount.times_used = 100
        self.discount.save()
        
        self.assertFalse(self.discount.is_valid)


class TicketAPITest(APITestCase):
    """Tests para la API de tickets"""
    
    def setUp(self):
        self.client = APIClient()
        
        self.user = User.objects.create_user(
            username='buyer',
            email='buyer@test.com',
            password='testpass123'
        )
        
        organizer = User.objects.create_user(username='organizer', password='pass123')
        category = Category.objects.create(name="Conciertos")
        venue = Venue.objects.create(
            name="Arena", address="Calle Principal", city="Barranquilla",
            state="Atlántico", capacity=2000
        )
        
        now = timezone.now()
        
        self.event = Event.objects.create(
            title="Concierto Pop",
            description="Gran concierto",
            category=category,
            venue=venue,
            organizer=organizer,
            start_date=now + timedelta(days=45),
            end_date=now + timedelta(days=45, hours=5),
            registration_start=now,
            registration_end=now + timedelta(days=44),
            status='published',
            is_published=True
        )
        
        self.ticket_type = TicketType.objects.create(
            event=self.event,
            name="General",
            price=Decimal('80000.00'),
            quantity_available=500,
            sale_start=now,
            sale_end=now + timedelta(days=44),
            max_per_order=5
        )
    
    def test_list_ticket_types(self):
        """Test listar tipos de tickets"""
        response = self.client.get('/api/ticket-types/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_purchase_ticket_authenticated(self):
        """Test comprar ticket autenticado"""
        self.client.force_authenticate(user=self.user)
        
        data = {
            'ticket_type_id': self.ticket_type.id,
            'quantity': 2,
            'payment_method': 'credit_card'
        }
        
        response = self.client.post('/api/tickets/purchase/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data['tickets']), 2)
    
    def test_purchase_ticket_unauthenticated(self):
        """Test comprar ticket sin autenticación"""
        data = {
            'ticket_type_id': self.ticket_type.id,
            'quantity': 1,
            'payment_method': 'credit_card'
        }
        
        response = self.client.post('/api/tickets/purchase/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_my_tickets(self):
        """Test obtener mis tickets"""
        self.client.force_authenticate(user=self.user)
        
        # Crear ticket
        Ticket.objects.create(
            ticket_type=self.ticket_type,
            buyer=self.user,
            original_price=Decimal('80000.00'),
            final_price=Decimal('80000.00'),
            status='paid'
        )
        
        response = self.client.get('/api/tickets/my_tickets/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)
    
    def test_validate_discount_code(self):
        """Test validar código de descuento"""
        now = timezone.now()
        
        discount = DiscountCode.objects.create(
            code="TEST20",
            discount_type="percentage",
            discount_value=Decimal('20.00'),
            event=self.event,
            valid_from=now,
            valid_until=now + timedelta(days=30),
            is_active=True
        )
        
        data = {
            'code': 'TEST20',
            'ticket_type_id': self.ticket_type.id
        }
        
        response = self.client.post('/api/discount-codes/verify/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['valid'])