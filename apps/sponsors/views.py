from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from django.db.models import Sum, Count, Q

from .models import SponsorTier, Sponsor, Sponsorship, SponsorBenefit
from .serializers import (
    SponsorTierSerializer, SponsorListSerializer, SponsorDetailSerializer,
    SponsorshipListSerializer, SponsorshipDetailSerializer,
    SponsorshipPaymentSerializer, SponsorBenefitSerializer,
    SponsorStatisticsSerializer
)
from .filters import SponsorFilter, SponsorshipFilter
from config.permissions import IsSponsorManagerOrReadOnly


class SponsorTierViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar niveles de patrocinio
    
    list: Listar niveles de patrocinio
    retrieve: Obtener detalle de un nivel
    create: Crear nuevo nivel (solo admin)
    update: Actualizar nivel (solo admin)
    destroy: Eliminar nivel (solo admin)
    """
    queryset = SponsorTier.objects.filter(is_active=True)
    serializer_class = SponsorTierSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['priority_level', 'min_contribution', 'display_order']
    ordering = ['-priority_level', 'display_order']
    
    @action(detail=False, methods=['get'])
    def public(self, request):
        """
        Endpoint personalizado: Niveles públicos para mostrar a potenciales sponsors
        GET /api/sponsor-tiers/public/
        """
        tiers = self.get_queryset().filter(is_active=True)
        serializer = self.get_serializer(tiers, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def sponsors(self, request, pk=None):
        """
        Endpoint personalizado: Patrocinadores en este nivel
        GET /api/sponsor-tiers/{id}/sponsors/
        """
        tier = self.get_object()
        sponsors = tier.sponsors.filter(is_active=True)
        
        serializer = SponsorListSerializer(sponsors, many=True)
        return Response(serializer.data)


class SponsorViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar patrocinadores
    
    list: Listar patrocinadores
    retrieve: Obtener detalle de un patrocinador
    create: Crear nuevo patrocinador
    update: Actualizar patrocinador
    destroy: Eliminar patrocinador
    """
    queryset = Sponsor.objects.filter(is_active=True).select_related('tier')
    permission_classes = [IsSponsorManagerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = SponsorFilter
    search_fields = ['name', 'industry', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_serializer_class(self):
        """Usar serializer diferente según la acción"""
        if self.action == 'list':
            return SponsorListSerializer
        return SponsorDetailSerializer
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """
        Endpoint personalizado: Patrocinadores destacados
        GET /api/sponsors/featured/
        """
        sponsors = self.get_queryset().filter(
            tier__homepage_featured=True,
            status='active'
        ).order_by('-tier__priority_level')[:10]
        
        serializer = SponsorListSerializer(sponsors, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_industry(self, request):
        """
        Endpoint personalizado: Patrocinadores agrupados por industria
        GET /api/sponsors/by_industry/
        """
        industries = Sponsor.objects.filter(
            is_active=True
        ).values('industry').annotate(
            count=Count('id')
        ).order_by('-count')
        
        return Response(industries)
    
    @action(detail=True, methods=['get'])
    def sponsorships(self, request, pk=None):
        """
        Endpoint personalizado: Patrocinios de este sponsor
        GET /api/sponsors/{id}/sponsorships/
        """
        sponsor = self.get_object()
        sponsorships = sponsor.sponsorships.filter(is_active=True)
        
        serializer = SponsorshipListSerializer(sponsorships, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def contribution_summary(self, request, pk=None):
        """
        Endpoint personalizado: Resumen de contribuciones del sponsor
        GET /api/sponsors/{id}/contribution_summary/
        """
        sponsor = self.get_object()
        
        sponsorships = sponsor.sponsorships.filter(is_active=True)
        
        summary = {
            'total_contribution': sponsorships.aggregate(
                total=Sum('contribution_amount')
            )['total'] or 0,
            'total_paid': sponsorships.aggregate(
                total=Sum('amount_paid')
            )['total'] or 0,
            'pending_balance': sponsorships.aggregate(
                total=Sum('contribution_amount')
            )['total'] or 0,
            'active_sponsorships': sponsorships.count(),
            'events_sponsored': sponsorships.values('event').distinct().count(),
            'payment_status_breakdown': {
                'completed': sponsorships.filter(payment_status='completed').count(),
                'partial': sponsorships.filter(payment_status='partial').count(),
                'pending': sponsorships.filter(payment_status='pending').count(),
            }
        }
        
        # Calcular balance pendiente real
        summary['pending_balance'] = summary['total_contribution'] - summary['total_paid']
        
        return Response(summary)


class SponsorshipViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar patrocinios
    
    list: Listar patrocinios
    retrieve: Obtener detalle de un patrocinio
    create: Crear nuevo patrocinio
    update: Actualizar patrocinio
    destroy: Eliminar patrocinio
    """
    queryset = Sponsorship.objects.filter(is_active=True).select_related(
        'sponsor', 'event', 'tier'
    )
    permission_classes = [IsSponsorManagerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = SponsorshipFilter
    search_fields = ['sponsor__name', 'event__title']
    ordering_fields = ['contribution_amount', 'created_at']
    ordering = ['-contribution_amount']
    
    def get_serializer_class(self):
        """Usar serializer diferente según la acción"""
        if self.action == 'list':
            return SponsorshipListSerializer
        elif self.action == 'register_payment':
            return SponsorshipPaymentSerializer
        return SponsorshipDetailSerializer
    
    @action(detail=False, methods=['get'])
    def by_event(self, request):
        """
        Endpoint personalizado: Patrocinios por evento
        GET /api/sponsorships/by_event/?event_id=1
        """
        event_id = request.query_params.get('event_id')
        
        if not event_id:
            return Response(
                {'error': 'Debe proporcionar event_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        sponsorships = self.get_queryset().filter(
            event_id=event_id,
            is_public=True
        ).order_by('-tier__priority_level', '-contribution_amount')
        
        serializer = SponsorshipListSerializer(sponsorships, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending_payments(self, request):
        """
        Endpoint personalizado: Patrocinios con pagos pendientes
        GET /api/sponsorships/pending_payments/
        """
        sponsorships = self.get_queryset().filter(
            Q(payment_status='pending') | Q(payment_status='partial')
        ).order_by('payment_due_date')
        
        serializer = SponsorshipListSerializer(sponsorships, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    @transaction.atomic
    def register_payment(self, request, pk=None):
        """
        Endpoint personalizado: Registrar pago de patrocinio
        POST /api/sponsorships/{id}/register_payment/
        Body: {
            "payment_amount": 5000.00,
            "payment_date": "2024-12-15",
            "payment_method": "Transferencia bancaria",
            "notes": "Pago parcial 1/3"
        }
        """
        sponsorship = self.get_object()
        
        # Agregar sponsorship_id al data
        data = request.data.copy()
        data['sponsorship_id'] = sponsorship.id
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        updated_sponsorship = serializer.save()
        
        return Response({
            'success': True,
            'message': 'Pago registrado exitosamente',
            'sponsorship': SponsorshipDetailSerializer(updated_sponsorship).data
        })
    
    @action(detail=True, methods=['post'])
    def mark_completed(self, request, pk=None):
        """
        Endpoint personalizado: Marcar patrocinio como completado
        POST /api/sponsorships/{id}/mark_completed/
        """
        sponsorship = self.get_object()
        
        if sponsorship.remaining_balance > 0:
            return Response(
                {
                    'error': f'Aún hay un balance pendiente de ${sponsorship.remaining_balance:,.2f}'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        sponsorship.payment_status = 'completed'
        sponsorship.save()
        
        return Response({
            'success': True,
            'message': 'Patrocinio marcado como completado'
        })
    
    @action(detail=True, methods=['get'])
    def benefits(self, request, pk=None):
        """
        Endpoint personalizado: Beneficios del patrocinio
        GET /api/sponsorships/{id}/benefits/
        """
        sponsorship = self.get_object()
        benefits = sponsorship.delivered_benefits.all()
        
        serializer = SponsorBenefitSerializer(benefits, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Endpoint personalizado: Estadísticas generales de patrocinios
        GET /api/sponsorships/statistics/
        """
        queryset = self.get_queryset()
        
        # Filtro opcional por evento
        event_id = request.query_params.get('event_id')
        if event_id:
            queryset = queryset.filter(event_id=event_id)
        
        total_contribution = queryset.aggregate(
            total=Sum('contribution_amount')
        )['total'] or 0
        
        total_paid = queryset.aggregate(
            total=Sum('amount_paid')
        )['total'] or 0
        
        stats = {
            'total_sponsors': queryset.values('sponsor').distinct().count(),
            'active_sponsors': queryset.filter(
                sponsor__status='active'
            ).values('sponsor').distinct().count(),
            'total_contribution': total_contribution,
            'total_paid': total_paid,
            'pending_balance': total_contribution - total_paid,
            'sponsors_by_tier': {},
            'top_contributors': []
        }
        
        # Patrocinadores por tier
        tiers = queryset.values(
            'tier__name'
        ).annotate(
            count=Count('id')
        ).order_by('-count')
        
        stats['sponsors_by_tier'] = {
            tier['tier__name']: tier['count'] for tier in tiers
        }
        
        # Top contribuyentes
        top = queryset.values(
            'sponsor__name', 'sponsor__id'
        ).annotate(
            total=Sum('contribution_amount')
        ).order_by('-total')[:5]
        
        stats['top_contributors'] = [
            {
                'id': item['sponsor__id'],
                'name': item['sponsor__name'],
                'total_contribution': float(item['total'])
            }
            for item in top
        ]
        
        serializer = SponsorStatisticsSerializer(stats)
        return Response(serializer.data)


class SponsorBenefitViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar beneficios de patrocinadores
    
    list: Listar beneficios
    retrieve: Obtener detalle de un beneficio
    create: Crear nuevo beneficio
    update: Actualizar beneficio
    destroy: Eliminar beneficio
    """
    queryset = SponsorBenefit.objects.all().select_related(
        'sponsorship', 'sponsorship__sponsor', 'sponsorship__event'
    )
    serializer_class = SponsorBenefitSerializer
    permission_classes = [IsSponsorManagerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ['created_at', 'delivered_date']
    ordering = ['-created_at']
    
    @action(detail=True, methods=['post'])
    def mark_delivered(self, request, pk=None):
        """
        Endpoint personalizado: Marcar beneficio como entregado
        POST /api/sponsor-benefits/{id}/mark_delivered/
        Body: {
            "notes": "Entregado el logo en el banner principal"
        }
        """
        benefit = self.get_object()
        
        from django.utils import timezone
        
        benefit.is_delivered = True
        benefit.delivered_date = timezone.now().date()
        benefit.delivered_by = request.user
        benefit.notes = request.data.get('notes', benefit.notes)
        benefit.save()
        
        return Response({
            'success': True,
            'message': 'Beneficio marcado como entregado',
            'benefit': SponsorBenefitSerializer(benefit).data
        })
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """
        Endpoint personalizado: Beneficios pendientes de entrega
        GET /api/sponsor-benefits/pending/
        """
        benefits = self.get_queryset().filter(is_delivered=False)
        
        # Filtro opcional por patrocinio
        sponsorship_id = request.query_params.get('sponsorship_id')
        if sponsorship_id:
            benefits = benefits.filter(sponsorship_id=sponsorship_id)
        
        serializer = self.get_serializer(benefits, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_sponsorship(self, request):
        """
        Endpoint personalizado: Beneficios por patrocinio
        GET /api/sponsor-benefits/by_sponsorship/?sponsorship_id=1
        """
        sponsorship_id = request.query_params.get('sponsorship_id')
        
        if not sponsorship_id:
            return Response(
                {'error': 'Debe proporcionar sponsorship_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        benefits = self.get_queryset().filter(sponsorship_id=sponsorship_id)
        serializer = self.get_serializer(benefits, many=True)
        
        return Response({
            'total_benefits': benefits.count(),
            'delivered': benefits.filter(is_delivered=True).count(),
            'pending': benefits.filter(is_delivered=False).count(),
            'benefits': serializer.data
        })