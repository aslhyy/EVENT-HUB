from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SponsorTierViewSet, SponsorViewSet,
    SponsorshipViewSet, SponsorBenefitViewSet
)

router = DefaultRouter()
router.register(r'sponsor-tiers', SponsorTierViewSet, basename='sponsortier')
router.register(r'sponsors', SponsorViewSet, basename='sponsor')
router.register(r'sponsorships', SponsorshipViewSet, basename='sponsorship')
router.register(r'sponsor-benefits', SponsorBenefitViewSet, basename='sponsorbenefit')

urlpatterns = [
    path('', include(router.urls)),
]