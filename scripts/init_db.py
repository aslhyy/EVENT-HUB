"""
Script para inicializar la base de datos con datos de prueba
Ejecutar: python manage.py shell < scripts/init_db.py
"""

import os
import django
from datetime import timedelta
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from apps.events.models import Category, Venue, Event
from apps.tickets.models import TicketType, DiscountCode
from apps.attendees.models import Attendee
from apps.sponsors.models import SponsorTier, Sponsor, Sponsorship

print("🚀 Iniciando creación de datos de prueba...")

# ============= USUARIOS =============
print("\n👤 Creando usuarios...")

admin_user, created = User.objects.get_or_create(
    username='admin',
    defaults={
        'email': 'admin@eventhub.com',
        'is_staff': True,
        'is_superuser': True,
        'first_name': 'Admin',
        'last_name': 'EventHub'
    }
)
if created:
    admin_user.set_password('admin123')
    admin_user.save()
    print("✅ Usuario admin creado")

# Sarah
sarah, created = User.objects.get_or_create(
    username='sarah',
    defaults={
        'email': 'sarah@eventhub.com',
        'first_name': 'Sarah',
        'last_name': 'García'
    }
)
if created:
    sarah.set_password('sarah123')
    sarah.save()
    print("✅ Usuario Sarah creado")

# Karen
karen, created = User.objects.get_or_create(
    username='karen',
    defaults={
        'email': 'karen@eventhub.com',
        'first_name': 'Karen',
        'last_name': 'Rodríguez'
    }
)
if created:
    karen.set_password('karen123')
    karen.save()
    print("✅ Usuario Karen creado")

# Neyireth
neyireth, created = User.objects.get_or_create(
    username='neyireth',
    defaults={
        'email': 'neyireth@eventhub.com',
        'first_name': 'Neyireth',
        'last_name': 'López'
    }
)
if created:
    neyireth.set_password('neyireth123')
    neyireth.save()
    print("✅ Usuario Neyireth creado")

# Aslhy (Líder)
aslhy, created = User.objects.get_or_create(
    username='aslhy',
    defaults={
        'email': 'aslhy@eventhub.com',
        'first_name': 'Aslhy',
        'last_name': 'Martínez',
        'is_staff': True
    }
)
if created:
    aslhy.set_password('aslhy123')
    aslhy.save()
    print("✅ Usuario Aslhy (Líder) creado")

# ============= CATEGORÍAS =============
print("\n📂 Creando categorías...")

categories_data = [
    {'name': 'Música', 'icon': 'fa-music', 'description': 'Conciertos y festivales musicales'},
    {'name': 'Tecnología', 'icon': 'fa-laptop', 'description': 'Conferencias y eventos tech'},
    {'name': 'Deportes', 'icon': 'fa-futbol', 'description': 'Eventos deportivos'},
    {'name': 'Arte y Cultura', 'icon': 'fa-palette', 'description': 'Exposiciones y eventos culturales'},
    {'name': 'Negocios', 'icon': 'fa-briefcase', 'description': 'Conferencias empresariales'},
    {'name': 'Educación', 'icon': 'fa-graduation-cap', 'description': 'Talleres y seminarios'},
]

categories = {}
for cat_data in categories_data:
    category, created = Category.objects.get_or_create(
        name=cat_data['name'],
        defaults={
            'icon': cat_data['icon'],
            'description': cat_data['description'],
            'is_active': True
        }
    )
    categories[cat_data['name']] = category
    if created:
        print(f"✅ Categoría '{cat_data['name']}' creada")

# ============= LUGARES =============
print("\n📍 Creando lugares...")

venues_data = [
    {
        'name': 'Centro de Convenciones Gonzalo Jiménez de Quesada',
        'address': 'Carrera 7 #32-16',
        'city': 'Bogotá',
        'state': 'Cundinamarca',
        'capacity': 2000,
        'facilities': 'WiFi, Parking, Aire acondicionado, Catering'
    },
    {
        'name': 'Teatro Colón',
        'address': 'Calle 10 #5-32',
        'city': 'Bogotá',
        'state': 'Cundinamarca',
        'capacity': 800,
        'facilities': 'Sistema de sonido profesional, Iluminación, Camerinos'
    },
    {
        'name': 'Movistar Arena',
        'address': 'Carrera 68 #51-23',
        'city': 'Bogotá',
        'state': 'Cundinamarca',
        'capacity': 15000,
        'facilities': 'Pantallas gigantes, Parking, Seguridad, Food court'
    },
    {
        'name': 'Auditorio Universidad Nacional',
        'address': 'Carrera 45 #26-85',
        'city': 'Bogotá',
        'state': 'Cundinamarca',
        'capacity': 500,
        'facilities': 'Proyector, WiFi, Aire acondicionado'
    },
]

venues = {}
for venue_data in venues_data:
    venue, created = Venue.objects.get_or_create(
        name=venue_data['name'],
        defaults=venue_data
    )
    venues[venue_data['name']] = venue
    if created:
        print(f"✅ Lugar '{venue_data['name']}' creado")

# ============= EVENTOS =============
print("\n🎉 Creando eventos...")

now = timezone.now()

events_data = [
    {
        'title': 'Festival de Rock Bogotá 2025',
        'description': 'El festival de rock más grande de Colombia con bandas nacionales e internacionales.',
        'short_description': 'Festival de rock con las mejores bandas',
        'category': categories['Música'],
        'venue': venues['Movistar Arena'],
        'organizer': sarah,
        'start_date': now + timedelta(days=60),
        'end_date': now + timedelta(days=60, hours=8),
        'registration_start': now,
        'registration_end': now + timedelta(days=59),
        'is_free': False,
        'max_attendees': 10000,
        'status': 'published',
        'is_published': True,
        'is_featured': True,
        'tags': 'rock, música, festival, concierto'
    },
    {
        'title': 'TechSummit Colombia 2025',
        'description': 'Conferencia de tecnología con expertos internacionales en IA, Cloud y Desarrollo.',
        'short_description': 'La mayor conferencia tech del país',
        'category': categories['Tecnología'],
        'venue': venues['Centro de Convenciones Gonzalo Jiménez de Quesada'],
        'organizer': karen,
        'start_date': now + timedelta(days=45),
        'end_date': now + timedelta(days=47),
        'registration_start': now,
        'registration_end': now + timedelta(days=40),
        'is_free': False,
        'max_attendees': 1500,
        'status': 'published',
        'is_published': True,
        'is_featured': True,
        'tags': 'tecnología, IA, desarrollo, conferencia'
    },
    {
        'title': 'Maratón Internacional Bogotá',
        'description': '42K por las calles de Bogotá con corredores de todo el mundo.',
        'short_description': 'Maratón internacional 42K',
        'category': categories['Deportes'],
        'venue': venues['Movistar Arena'],
        'organizer': neyireth,
        'start_date': now + timedelta(days=90),
        'end_date': now + timedelta(days=90, hours=6),
        'registration_start': now,
        'registration_end': now + timedelta(days=80),
        'is_free': False,
        'max_attendees': 5000,
        'status': 'published',
        'is_published': True,
        'tags': 'deportes, maratón, running, 42k'
    },
    {
        'title': 'Exposición: Arte Contemporáneo Latinoamericano',
        'description': 'Muestra de arte contemporáneo con artistas de toda América Latina.',
        'short_description': 'Exposición de arte latinoamericano',
        'category': categories['Arte y Cultura'],
        'venue': venues['Teatro Colón'],
        'organizer': aslhy,
        'start_date': now + timedelta(days=30),
        'end_date': now + timedelta(days=60),
        'registration_start': now,
        'registration_end': now + timedelta(days=59),
        'is_free': True,
        'max_attendees': 500,
        'status': 'published',
        'is_published': True,
        'tags': 'arte, cultura, exposición, latinoamérica'
    },
]

events = []
for event_data in events_data:
    event, created = Event.objects.get_or_create(
        title=event_data['title'],
        defaults=event_data
    )
    events.append(event)
    if created:
        print(f"✅ Evento '{event_data['title']}' creado")

# ============= TIPOS DE TICKETS =============
print("\n🎫 Creando tipos de tickets...")

for event in events:
    if not event.is_free:
        # VIP
        TicketType.objects.get_or_create(
            event=event,
            name='VIP',
            defaults={
                'description': 'Acceso VIP con beneficios exclusivos',
                'price': Decimal('250000.00'),
                'quantity_available': 100,
                'quantity_sold': 0,
                'max_per_order': 4,
                'sale_start': event.registration_start,
                'sale_end': event.registration_end,
                'includes_food': True,
                'includes_drink': True,
                'includes_parking': True,
                'display_order': 1
            }
        )
        
        # General
        TicketType.objects.get_or_create(
            event=event,
            name='General',
            defaults={
                'description': 'Entrada general al evento',
                'price': Decimal('120000.00'),
                'quantity_available': 500,
                'quantity_sold': 0,
                'max_per_order': 6,
                'sale_start': event.registration_start,
                'sale_end': event.registration_end,
                'includes_food': False,
                'includes_drink': True,
                'includes_parking': False,
                'display_order': 2
            }
        )
        
        print(f"✅ Tickets para '{event.title}' creados")

# ============= CÓDIGOS DE DESCUENTO =============
print("\n💰 Creando códigos de descuento...")

for event in events[:2]:  # Solo para los primeros 2 eventos
    DiscountCode.objects.get_or_create(
        code=f'EARLYBIRD{event.id}',
        defaults={
            'description': 'Descuento por compra anticipada',
            'discount_type': 'percentage',
            'discount_value': Decimal('20.00'),
            'event': event,
            'max_uses': 100,
            'times_used': 0,
            'valid_from': now,
            'valid_until': now + timedelta(days=15),
            'is_active': True
        }
    )
    print(f"✅ Código EARLYBIRD{event.id} creado")

# ============= SPONSOR TIERS =============
print("\n🏆 Creando niveles de patrocinio...")

tiers_data = [
    {
        'name': 'Platinum',
        'min_contribution': Decimal('50000000.00'),
        'benefits': 'Logo gigante\nStand premium\n10 tickets VIP\nMención en todos los materiales',
        'priority_level': 100,
        'logo_size': 'xlarge',
        'homepage_featured': True,
        'speaking_opportunity': True,
        'booth_space': True,
        'complimentary_tickets': 10,
        'vip_tickets': 10,
        'color': '#E5E4E2'
    },
    {
        'name': 'Gold',
        'min_contribution': Decimal('30000000.00'),
        'benefits': 'Logo grande\nStand estándar\n6 tickets VIP\nMención en redes sociales',
        'priority_level': 80,
        'logo_size': 'large',
        'homepage_featured': True,
        'speaking_opportunity': True,
        'booth_space': True,
        'complimentary_tickets': 6,
        'vip_tickets': 6,
        'color': '#FFD700'
    },
    {
        'name': 'Silver',
        'min_contribution': Decimal('15000000.00'),
        'benefits': 'Logo mediano\n4 tickets general\nMención en programa',
        'priority_level': 60,
        'logo_size': 'medium',
        'homepage_featured': False,
        'speaking_opportunity': False,
        'booth_space': True,
        'complimentary_tickets': 4,
        'vip_tickets': 0,
        'color': '#C0C0C0'
    },
    {
        'name': 'Bronze',
        'min_contribution': Decimal('5000000.00'),
        'benefits': 'Logo pequeño\n2 tickets general',
        'priority_level': 40,
        'logo_size': 'small',
        'homepage_featured': False,
        'speaking_opportunity': False,
        'booth_space': False,
        'complimentary_tickets': 2,
        'vip_tickets': 0,
        'color': '#CD7F32'
    },
]

tiers = {}
for tier_data in tiers_data:
    tier, created = SponsorTier.objects.get_or_create(
        name=tier_data['name'],
        defaults=tier_data
    )
    tiers[tier_data['name']] = tier
    if created:
        print(f"✅ Tier '{tier_data['name']}' creado")

# ============= SPONSORS =============
print("\n🤝 Creando patrocinadores...")

sponsors_data = [
    {
        'name': 'TechCorp Colombia',
        'description': 'Líder en soluciones tecnológicas empresariales',
        'industry': 'Tecnología',
        'contact_person': 'Juan Pérez',
        'contact_email': 'juan@techcorp.com',
        'contact_phone': '+573001234567',
        'website': 'https://techcorp.com',
        'tier': tiers['Gold'],
        'status': 'active'
    },
    {
        'name': 'Banco Nacional',
        'description': 'Entidad financiera líder en Colombia',
        'industry': 'Finanzas',
        'contact_person': 'María González',
        'contact_email': 'maria@banconacional.com',
        'contact_phone': '+573007654321',
        'website': 'https://banconacional.com',
        'tier': tiers['Platinum'],
        'status': 'active'
    },
    {
        'name': 'Café Premium',
        'description': 'Productores de café colombiano de exportación',
        'industry': 'Alimentos y Bebidas',
        'contact_person': 'Carlos Ramírez',
        'contact_email': 'carlos@cafepremium.com',
        'contact_phone': '+573009876543',
        'website': 'https://cafepremium.com',
        'tier': tiers['Silver'],
        'status': 'active'
    },
]

sponsors = []
for sponsor_data in sponsors_data:
    sponsor, created = Sponsor.objects.get_or_create(
        name=sponsor_data['name'],
        defaults=sponsor_data
    )
    sponsors.append(sponsor)
    if created:
        print(f"✅ Sponsor '{sponsor_data['name']}' creado")

# ============= SPONSORSHIPS =============
print("\n💼 Creando patrocinios...")

for i, sponsor in enumerate(sponsors):
    if i < len(events):
        event = events[i]
        Sponsorship.objects.get_or_create(
            sponsor=sponsor,
            event=event,
            defaults={
                'tier': sponsor.tier,
                'contribution_amount': sponsor.tier.min_contribution,
                'amount_paid': sponsor.tier.min_contribution * Decimal('0.5'),
                'payment_status': 'partial',
                'is_active': True,
                'is_public': True
            }
        )
        print(f"✅ Patrocinio de '{sponsor.name}' para '{event.title}' creado")

print("\n✅ ¡Datos de prueba creados exitosamente!")
print("\n📝 Credenciales de acceso:")
print("=" * 50)
print("Admin: username='admin', password='admin123'")
print("Sarah: username='sarah', password='sarah123'")
print("Karen: username='karen', password='karen123'")
print("Neyireth: username='neyireth', password='neyireth123'")
print("Aslhy (Líder): username='aslhy', password='aslhy123'")
print("=" * 50)