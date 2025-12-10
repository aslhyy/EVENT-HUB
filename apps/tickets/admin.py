from django.contrib import admin
from .models import TicketType, Ticket, DiscountCode


@admin.register(TicketType)
class TicketTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'event', 'price', 'quantity_available', 'quantity_sold', 'is_active']
    list_filter = ['is_active', 'event__category']
    search_fields = ['name', 'event__title']
    ordering = ['event', 'display_order']


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['ticket_code', 'ticket_type', 'buyer', 'status', 'purchase_date', 'final_price']
    list_filter = ['status', 'purchase_date']
    search_fields = ['ticket_code', 'buyer__username', 'transaction_id']
    date_hierarchy = 'purchase_date'
    ordering = ['-purchase_date']
    readonly_fields = ['ticket_code', 'qr_code']


@admin.register(DiscountCode)
class DiscountCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_type', 'discount_value', 'times_used', 'max_uses', 'is_active']
    list_filter = ['discount_type', 'is_active']
    search_fields = ['code', 'description']