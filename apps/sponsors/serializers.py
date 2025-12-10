from rest_framework import serializers
from django.db import transaction
from apps.events.models import Event
from .models import SponsorTier, Sponsor, Sponsorship, SponsorBenefit


class SponsorTierSerializer(serializers.ModelSerializer):
    """Serializer para niveles de patrocinio"""

    sponsors_count = serializers.SerializerMethodField()
    contribution_range = serializers.SerializerMethodField()

    class Meta:
        model = SponsorTier
        fields = [
            "id",
            "name",
            "description",
            "min_contribution",
            "max_contribution",
            "contribution_range",
            "benefits",
            "priority_level",
            "logo_size",
            "homepage_featured",
            "speaking_opportunity",
            "booth_space",
            "complimentary_tickets",
            "vip_tickets",
            "color",
            "icon",
            "display_order",
            "is_active",
            "sponsors_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def get_sponsors_count(self, obj):
        """Cantidad de patrocinadores en este nivel"""
        return obj.sponsors.filter(is_active=True).count()

    def get_contribution_range(self, obj):
        """Rango de contribución formateado"""
        if obj.max_contribution:
            return f"${obj.min_contribution:,.2f} - ${obj.max_contribution:,.2f}"
        return f"${obj.min_contribution:,.2f}+"

    def validate(self, data):
        """Validaciones del nivel de patrocinio"""
        if "max_contribution" in data and data["max_contribution"]:
            if data["max_contribution"] <= data.get("min_contribution", 0):
                raise serializers.ValidationError(
                    "La contribución máxima debe ser mayor a la mínima"
                )

        if "color" in data:
            color = data["color"]
            if not color.startswith("#") or len(color) != 7:
                raise serializers.ValidationError(
                    "El color debe estar en formato hexadecimal (#RRGGBB)"
                )

        return data


class SponsorListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listado de patrocinadores"""

    tier_name = serializers.CharField(source="tier.name", read_only=True)
    active_sponsorships = serializers.SerializerMethodField()

    class Meta:
        model = Sponsor
        fields = [
            "id",
            "name",
            "slug",
            "industry",
            "tier_name",
            "logo",
            "status",
            "is_active",
            "active_sponsorships",
        ]

    def get_active_sponsorships(self, obj):
        """Cantidad de patrocinios activos"""
        return obj.sponsorships.filter(is_active=True).count()


class SponsorDetailSerializer(serializers.ModelSerializer):
    """Serializer detallado para patrocinadores"""

    tier_detail = SponsorTierSerializer(source="tier", read_only=True)
    tier_id = serializers.PrimaryKeyRelatedField(
        queryset=SponsorTier.objects.all(),
        source="tier",
        write_only=True,
        required=False,
    )
    account_manager_name = serializers.CharField(
        source="account_manager.username", read_only=True
    )
    total_contribution = serializers.SerializerMethodField()
    sponsored_events = serializers.SerializerMethodField()

    class Meta:
        model = Sponsor
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "industry",
            "contact_person",
            "contact_email",
            "contact_phone",
            "website",
            "linkedin_url",
            "twitter_url",
            "instagram_url",
            "facebook_url",
            "logo",
            "banner_image",
            "tier_detail",
            "tier_id",
            "status",
            "is_active",
            "account_manager",
            "account_manager_name",
            "total_contribution",
            "sponsored_events",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["slug", "created_at", "updated_at"]

    def get_total_contribution(self, obj):
        """Total de contribuciones realizadas"""
        return sum(
            sponsorship.contribution_amount
            for sponsorship in obj.sponsorships.filter(is_active=True)
        )

    def get_sponsored_events(self, obj):
        """Lista de eventos patrocinados"""
        sponsorships = obj.sponsorships.filter(is_active=True).select_related("event")
        return [
            {
                "id": sp.event.id,
                "title": sp.event.title,
                "start_date": sp.event.start_date,
                "contribution": float(sp.contribution_amount),
                "tier": sp.tier.name,
            }
            for sp in sponsorships
        ]

    def validate_contact_email(self, value):
        """Validar email de contacto"""
        return value.lower()

    def validate_website(self, value):
        """Validar URL del sitio web"""
        if value and not value.startswith(("http://", "https://")):
            return f"https://{value}"
        return value


class SponsorBenefitSerializer(serializers.ModelSerializer):
    """Serializer para beneficios de patrocinadores"""

    sponsorship_info = serializers.SerializerMethodField()
    delivered_by_name = serializers.CharField(
        source="delivered_by.username", read_only=True
    )

    class Meta:
        model = SponsorBenefit
        fields = [
            "id",
            "sponsorship",
            "sponsorship_info",
            "benefit_name",
            "description",
            "is_delivered",
            "delivered_date",
            "delivered_by",
            "delivered_by_name",
            "proof_document",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def get_sponsorship_info(self, obj):
        """Información del patrocinio"""
        return {
            "sponsor_name": obj.sponsorship.sponsor.name,
            "event_title": obj.sponsorship.event.title,
            "tier": obj.sponsorship.tier.name,
        }

    def validate(self, data):
        """Validaciones del beneficio"""
        if data.get("is_delivered") and not data.get("delivered_date"):
            from django.utils import timezone

            data["delivered_date"] = timezone.now().date()

        if data.get("is_delivered") and not data.get("delivered_by"):
            data["delivered_by"] = self.context["request"].user

        return data


class SponsorshipListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listado de patrocinios"""

    sponsor_name = serializers.CharField(source="sponsor.name", read_only=True)
    event_title = serializers.CharField(source="event.title", read_only=True)
    tier_name = serializers.CharField(source="tier.name", read_only=True)
    remaining_balance = serializers.ReadOnlyField()
    payment_progress = serializers.SerializerMethodField()

    class Meta:
        model = Sponsorship
        fields = [
            "id",
            "sponsor_name",
            "event_title",
            "tier_name",
            "contribution_amount",
            "amount_paid",
            "remaining_balance",
            "payment_status",
            "payment_progress",
            "is_active",
        ]

    def get_payment_progress(self, obj):
        """Progreso de pago en porcentaje"""
        return round(obj.payment_progress_percentage, 2)


class SponsorshipDetailSerializer(serializers.ModelSerializer):
    """Serializer detallado para patrocinios"""
    sponsor_detail = SponsorListSerializer(source='sponsor', read_only=True)
    sponsor_id = serializers.PrimaryKeyRelatedField(
        queryset=Sponsor.objects.all(),
        source='sponsor',
        write_only=True
    )
    event_detail = serializers.SerializerMethodField()
    event_id = serializers.PrimaryKeyRelatedField(
        queryset=Event.objects.filter(is_published=True),  # ← CORRECCIÓN AQUÍ
        source='event',
        write_only=True
    )
    tier_detail = SponsorTierSerializer(source='tier', read_only=True)
    tier_id = serializers.PrimaryKeyRelatedField(
        queryset=SponsorTier.objects.all(),
        source='tier',
        write_only=True
    )
    remaining_balance = serializers.ReadOnlyField()
    payment_progress_percentage = serializers.ReadOnlyField()
    benefits = SponsorBenefitSerializer(
        source='delivered_benefits',
        many=True,
        read_only=True
    )
    
    class Meta:
        model = Sponsorship
        fields = [
            'id', 'sponsor', 'sponsor_id', 'sponsor_detail',
            'event', 'event_id', 'event_detail',
            'tier', 'tier_id', 'tier_detail',
            'contribution_amount', 'payment_status', 'amount_paid',
            'remaining_balance', 'payment_progress_percentage',
            'contract_signed_date', 'payment_due_date',
            'custom_benefits', 'booth_number', 'speaking_slot',
            'contract_document', 'is_active', 'is_public',
            'benefits', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_event_detail(self, obj):
        """Detalles del evento"""
        return {
            'id': obj.event.id,
            'title': obj.event.title,
            'start_date': obj.event.start_date,
            'end_date': obj.event.end_date,
            'venue_name': obj.event.venue.name,
            'status': obj.event.status,
        }
    
    def validate(self, data):
        """Validaciones del patrocinio"""
        # Validar que la contribución esté en el rango del tier
        if 'contribution_amount' in data and 'tier' in data:
            tier = data['tier']
            amount = data['contribution_amount']
            
            if amount < tier.min_contribution:
                raise serializers.ValidationError(
                    f"La contribución debe ser al menos ${tier.min_contribution:,.2f}"
                )
            
            if tier.max_contribution and amount > tier.max_contribution:
                raise serializers.ValidationError(
                    f"La contribución no puede exceder ${tier.max_contribution:,.2f}"
                )
        
        # Validar que no exista duplicado
        if self.instance is None:  # Solo en creación
            sponsor = data.get('sponsor')
            event = data.get('event')
            
            if Sponsorship.objects.filter(sponsor=sponsor, event=event).exists():
                raise serializers.ValidationError(
                    "Ya existe un patrocinio para este sponsor y evento"
                )
        
        # Validar montos de pago
        if 'amount_paid' in data and 'contribution_amount' in data:
            if data['amount_paid'] > data['contribution_amount']:
                raise serializers.ValidationError(
                    "El monto pagado no puede exceder el monto de contribución"
                )
        
        return data
    
    @transaction.atomic
    def create(self, validated_data):
        """Crear patrocinio y beneficios automáticos"""
        sponsorship = super().create(validated_data)
        
        # Crear beneficios automáticos basados en el tier
        tier_benefits = sponsorship.tier.benefits.split('\n')
        for benefit_name in tier_benefits:
            if benefit_name.strip():
                SponsorBenefit.objects.create(
                    sponsorship=sponsorship,
                    benefit_name=benefit_name.strip()
                )
        
        return sponsorship


class SponsorshipPaymentSerializer(serializers.Serializer):
    """Serializer para registrar pagos de patrocinio"""

    sponsorship_id = serializers.IntegerField()
    payment_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    payment_date = serializers.DateField(required=False)
    payment_method = serializers.CharField(max_length=100, required=False)
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate_sponsorship_id(self, value):
        """Validar que el patrocinio existe"""
        try:
            sponsorship = Sponsorship.objects.get(id=value)
            if not sponsorship.is_active:
                raise serializers.ValidationError("Este patrocinio no está activo")
        except Sponsorship.DoesNotExist:
            raise serializers.ValidationError("Patrocinio no encontrado")
        return value

    def validate(self, data):
        """Validaciones del pago"""
        sponsorship = Sponsorship.objects.get(id=data["sponsorship_id"])
        payment_amount = data["payment_amount"]

        # Validar que no exceda el monto pendiente
        remaining = sponsorship.remaining_balance
        if payment_amount > remaining:
            raise serializers.ValidationError(
                f"El pago (${payment_amount:,.2f}) excede el saldo pendiente (${remaining:,.2f})"
            )

        data["sponsorship"] = sponsorship
        return data

    @transaction.atomic
    def save(self):
        """Registrar el pago"""
        sponsorship = self.validated_data["sponsorship"]
        payment_amount = self.validated_data["payment_amount"]

        # Actualizar monto pagado
        sponsorship.amount_paid += payment_amount

        # Actualizar estado de pago
        if sponsorship.amount_paid >= sponsorship.contribution_amount:
            sponsorship.payment_status = "completed"
        elif sponsorship.amount_paid > 0:
            sponsorship.payment_status = "partial"

        sponsorship.save()

        return sponsorship


class SponsorStatisticsSerializer(serializers.Serializer):
    """Serializer para estadísticas de patrocinadores"""

    total_sponsors = serializers.IntegerField()
    active_sponsors = serializers.IntegerField()
    total_contribution = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_paid = serializers.DecimalField(max_digits=15, decimal_places=2)
    pending_balance = serializers.DecimalField(max_digits=15, decimal_places=2)
    sponsors_by_tier = serializers.DictField()
    top_contributors = serializers.ListField()
