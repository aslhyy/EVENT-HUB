from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TicketTypeViewSet, TicketViewSet, DiscountCodeViewSet

router = DefaultRouter()
router.register(r'ticket-types', TicketTypeViewSet, basename='tickettype')
router.register(r'tickets', TicketViewSet, basename='ticket')
router.register(r'discount-codes', DiscountCodeViewSet, basename='discountcode')

urlpatterns = [
    path('', include(router.urls)),
]