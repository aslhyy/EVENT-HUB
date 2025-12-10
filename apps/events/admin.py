from django.contrib import admin
from .models import Category, Venue, Event


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['name']


@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'state', 'capacity', 'is_active']
    list_filter = ['city', 'state', 'is_active']
    search_fields = ['name', 'city', 'address']
    ordering = ['name']
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'capacity', 'is_active')
        }),
        ('Ubicación', {
            'fields': ('address', 'city', 'state', 'country', 'postal_code', 'latitude', 'longitude')
        }),
        ('Contacto', {
            'fields': ('contact_phone', 'contact_email')
        }),
        ('Detalles', {
            'fields': ('facilities',)
        }),
    )


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'venue', 'organizer', 'start_date', 'status', 'is_published', 'is_featured']
    list_filter = ['status', 'is_published', 'is_featured', 'category', 'start_date']
    search_fields = ['title', 'description', 'tags']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'start_date'
    ordering = ['-start_date']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('title', 'slug', 'description', 'short_description', 'category', 'organizer')
        }),
        ('Ubicación y Fechas', {
            'fields': ('venue', 'start_date', 'end_date', 'registration_start', 'registration_end')
        }),
        ('Configuración', {
            'fields': ('is_free', 'max_attendees', 'status', 'is_published', 'is_featured')
        }),
        ('Multimedia', {
            'fields': ('banner_image', 'thumbnail_image', 'tags')
        }),
    )
    
    readonly_fields = ['views_count']