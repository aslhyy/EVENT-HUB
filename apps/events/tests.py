from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import Category, Venue, Event
from .serializers import EventDetailSerializer


class CategoryModelTest(TestCase):
    """Tests para el modelo Category"""
    
    def setUp(self):
        self.category = Category.objects.create(
            name="Música",
            description="Eventos musicales"
        )
    
    def test_category_creation(self):
        """Test crear categoría"""
        self.assertEqual(self.category.name, "Música")
        self.assertTrue(self.category.is_active)
        self.assertIsNotNone(self.category.slug)
    
    def test_slug_auto_generation(self):
        """Test generación automática de slug"""
        category = Category.objects.create(name="Tecnología y Ciencia")
        self.assertEqual(category.slug, "tecnologia-y-ciencia")
    
    def test_category_str(self):
        """Test método __str__"""
        self.assertEqual(str(self.category), "Música")


class VenueModelTest(TestCase):
    """Tests para el modelo Venue"""
    
    def setUp(self):
        self.venue = Venue.objects.create(
            name="Centro de Convenciones",
            address="Calle 123",
            city="Bogotá",
            state="Cundinamarca",
            capacity=1000
        )
    
    def test_venue_creation(self):
        """Test crear lugar"""
        self.assertEqual(self.venue.name, "Centro de Convenciones")
        self.assertEqual(self.venue.capacity, 1000)
        self.assertTrue(self.venue.is_active)
    
    def test_venue_str(self):
        """Test método __str__"""
        expected = "Centro de Convenciones - Bogotá"
        self.assertEqual(str(self.venue), expected)


class EventModelTest(TestCase):
    """Tests para el modelo Event"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='organizer',
            email='organizer@test.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(name="Deportes")
        
        self.venue = Venue.objects.create(
            name="Estadio",
            address="Av Principal",
            city="Medellín",
            state="Antioquia",
            capacity=5000
        )
        
        now = timezone.now()
        
        self.event = Event.objects.create(
            title="Partido de Fútbol",
            description="Partido amistoso",
            category=self.category,
            venue=self.venue,
            organizer=self.user,
            start_date=now + timedelta(days=7),
            end_date=now + timedelta(days=7, hours=2),
            registration_start=now,
            registration_end=now + timedelta(days=6),
            max_attendees=100,
            status='published',
            is_published=True
        )
    
    def test_event_creation(self):
        """Test crear evento"""
        self.assertEqual(self.event.title, "Partido de Fútbol")
        self.assertEqual(self.event.organizer, self.user)
        self.assertTrue(self.event.is_published)
    
    def test_slug_generation(self):
        """Test generación de slug"""
        self.assertIsNotNone(self.event.slug)
        self.assertIn("partido", self.event.slug.lower())
    
    def test_event_is_active(self):
        """Test propiedad is_active"""
        self.assertTrue(self.event.is_active)
    
    def test_available_spots(self):
        """Test cálculo de cupos disponibles"""
        self.assertEqual(self.event.available_spots, 100)


class EventAPITest(APITestCase):
    """Tests para la API de eventos"""
    
    def setUp(self):
        self.client = APIClient()
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(name="Tecnología")
        
        self.venue = Venue.objects.create(
            name="Auditorio Tech",
            address="Calle Tech 1",
            city="Bogotá",
            state="Cundinamarca",
            capacity=200
        )
        
        now = timezone.now()
        
        self.event = Event.objects.create(
            title="Conferencia Tech 2024",
            description="Evento tecnológico",
            category=self.category,
            venue=self.venue,
            organizer=self.user,
            start_date=now + timedelta(days=30),
            end_date=now + timedelta(days=30, hours=8),
            registration_start=now,
            registration_end=now + timedelta(days=29),
            status='published',
            is_published=True
        )
    
    def test_list_events(self):
        """Test listar eventos"""
        response = self.client.get('/api/events/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)
    
    def test_retrieve_event(self):
        """Test obtener detalle de evento"""
        response = self.client.get(f'/api/events/{self.event.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], self.event.title)
    
    def test_create_event_authenticated(self):
        """Test crear evento autenticado"""
        self.client.force_authenticate(user=self.user)
        
        now = timezone.now()
        
        data = {
            'title': 'Nuevo Evento',
            'description': 'Descripción del evento',
            'category_id': self.category.id,
            'venue_id': self.venue.id,
            'start_date': (now + timedelta(days=15)).isoformat(),
            'end_date': (now + timedelta(days=15, hours=4)).isoformat(),
            'registration_start': now.isoformat(),
            'registration_end': (now + timedelta(days=14)).isoformat(),
            'is_free': False,
        }
        
        response = self.client.post('/api/events/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_create_event_unauthenticated(self):
        """Test crear evento sin autenticación"""
        data = {'title': 'Evento Sin Auth'}
        response = self.client.post('/api/events/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_filter_events_by_category(self):
        """Test filtrar eventos por categoría"""
        response = self.client.get(f'/api/events/?category={self.category.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_search_events(self):
        """Test búsqueda de eventos"""
        response = self.client.get('/api/events/?search=Tech')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_upcoming_events_endpoint(self):
        """Test endpoint de eventos próximos"""
        response = self.client.get('/api/events/upcoming/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class EventSerializerTest(TestCase):
    """Tests para serializers de eventos"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.category = Category.objects.create(name="Arte")
        self.venue = Venue.objects.create(
            name="Galería",
            address="Calle Arte",
            city="Cali",
            state="Valle",
            capacity=50
        )
        
        now = timezone.now()
        
        self.event = Event.objects.create(
            title="Exposición de Arte",
            description="Arte contemporáneo",
            category=self.category,
            venue=self.venue,
            organizer=self.user,
            start_date=now + timedelta(days=10),
            end_date=now + timedelta(days=10, hours=6),
            registration_start=now,
            registration_end=now + timedelta(days=9),
            status='published',
            is_published=True
        )
    
    def test_event_serialization(self):
        """Test serialización de evento"""
        serializer = EventDetailSerializer(self.event)
        data = serializer.data
        
        self.assertEqual(data['title'], self.event.title)
        self.assertIn('category', data)
        self.assertIn('venue', data)