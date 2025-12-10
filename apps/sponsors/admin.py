from django.contrib import admin
from apps.sponsors.models import SponsorTier, Sponsor, Sponsorship, SponsorBenefit


@admin.register(SponsorTier)
class SponsorTierAdmin(admin.ModelAdmin):
    list_display = ['name', 'min_contribution', 'priority_level', 'complimentary_tickets', 'is_active']
    list_filter = ['is_active', 'homepage_featured']
    ordering = ['-priority_level']


@admin.register(Sponsor)
class SponsorAdmin(admin.ModelAdmin):
    list_display = ['name', 'industry', 'tier', 'status', 'is_active']
    list_filter = ['status', 'tier', 'is_active', 'industry']
    search_fields = ['name', 'industry', 'description']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Sponsorship)
class SponsorshipAdmin(admin.ModelAdmin):
    list_display = ['sponsor', 'event', 'tier', 'contribution_amount', 'payment_status', 'is_active']
    list_filter = ['payment_status', 'tier', 'is_active']
    search_fields = ['sponsor__name', 'event__title']
    ordering = ['-contribution_amount']


@admin.register(SponsorBenefit)
class SponsorBenefitAdmin(admin.ModelAdmin):
    list_display = ['benefit_name', 'sponsorship', 'is_delivered', 'delivered_date']
    list_filter = ['is_delivered', 'delivered_date']
    search_fields = ['benefit_name', 'sponsorship__sponsor__name']