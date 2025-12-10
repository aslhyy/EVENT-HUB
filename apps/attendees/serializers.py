from rest_framework import serializers
from django.utils import timezone
from .models import Attendee, CheckInLog, Survey, SurveyQuestion, SurveyResponse


class AttendeeListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listado de asistentes"""
    event_title = serializers.CharField(source='event.title', read_only=True)
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = Attendee
        fields = [
            'id', 'full_name', 'email', 'event_title',
            'status', 'registration_date', 'checked_in_at'
        ]


class AttendeeDetailSerializer(serializers.ModelSerializer):
    """Serializer detallado para asistentes"""
    event_info = serializers.SerializerMethodField()
    full_name = serializers.ReadOnlyField()
    ticket_info = serializers.SerializerMethodField()
    checkin_history = serializers.SerializerMethodField()
    
    class Meta:
        model = Attendee
        fields = [
            'id', 'user', 'event', 'event_info', 'first_name', 'last_name',
            'full_name', 'email', 'phone', 'company', 'job_title',
            'dietary_restrictions', 'special_requirements',
            'status', 'registration_date', 'confirmation_date',
            'checked_in_at', 'checked_in_by', 'receive_reminders',
            'receive_updates', 'ticket_info', 'checkin_history',
            'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'registration_date', 'confirmation_date', 'checked_in_at',
            'checked_in_by', 'created_at', 'updated_at'
        ]
    
    def get_event_info(self, obj):
        """Información del evento"""
        return {
            'id': obj.event.id,
            'title': obj.event.title,
            'start_date': obj.event.start_date,
            'end_date': obj.event.end_date,
            'venue_name': obj.event.venue.name,
            'venue_address': obj.event.venue.address,
        }
    
    def get_ticket_info(self, obj):
        """Información del ticket asociado"""
        if hasattr(obj, 'ticket') and obj.ticket:
            return {
                'ticket_code': str(obj.ticket.ticket_code),
                'ticket_type': obj.ticket.ticket_type.name,
                'price': float(obj.ticket.final_price),
                'status': obj.ticket.status,
            }
        return None
    
    def get_checkin_history(self, obj):
        """Historial de check-ins"""
        logs = obj.checkin_logs.order_by('-checked_in_at')[:5]
        return [
            {
                'date': log.checked_in_at,
                'location': log.location,
                'checked_by': log.checked_in_by.username if log.checked_in_by else None
            }
            for log in logs
        ]
    
    def validate_email(self, value):
        """Validar formato de email"""
        if not value:
            raise serializers.ValidationError("El email es obligatorio")
        return value.lower()
    
    def validate(self, data):
        """Validaciones del asistente"""
        # Validar que no esté duplicado
        if self.instance is None:  # Solo en creación
            event = data.get('event')
            user = data.get('user') or self.context['request'].user
            
            if Attendee.objects.filter(event=event, user=user).exists():
                raise serializers.ValidationError(
                    "Ya estás registrado en este evento"
                )
            
            # Verificar cupos disponibles
            if event.max_attendees:
                confirmed_count = event.attendees.filter(status='confirmed').count()
                if confirmed_count >= event.max_attendees:
                    raise serializers.ValidationError(
                        "El evento ha alcanzado su capacidad máxima"
                    )
        
        return data
    
    def create(self, validated_data):
        """Asignar usuario automáticamente si no se proporciona"""
        if 'user' not in validated_data:
            validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class CheckInSerializer(serializers.Serializer):
    """Serializer para realizar check-in"""
    attendee_id = serializers.IntegerField(required=False)
    ticket_code = serializers.UUIDField(required=False)
    location = serializers.CharField(max_length=200, required=False)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        """Validar que se proporcione attendee_id o ticket_code"""
        if not data.get('attendee_id') and not data.get('ticket_code'):
            raise serializers.ValidationError(
                "Debe proporcionar attendee_id o ticket_code"
            )
        
        # Validar asistente
        if 'attendee_id' in data:
            try:
                attendee = Attendee.objects.get(id=data['attendee_id'])
                
                if attendee.status == 'cancelled':
                    raise serializers.ValidationError(
                        "Este registro ha sido cancelado"
                    )
                
                if attendee.status == 'checked_in':
                    raise serializers.ValidationError(
                        f"Ya realizó check-in el {attendee.checked_in_at.strftime('%Y-%m-%d %H:%M')}"
                    )
                
                data['attendee'] = attendee
                
            except Attendee.DoesNotExist:
                raise serializers.ValidationError("Asistente no encontrado")
        
        # Validar por ticket
        elif 'ticket_code' in data:
            from apps.tickets.models import Ticket
            try:
                ticket = Ticket.objects.select_related('attendee').get(
                    ticket_code=data['ticket_code']
                )
                
                if not ticket.attendee:
                    raise serializers.ValidationError(
                        "Este ticket no tiene un asistente asociado"
                    )
                
                data['attendee'] = ticket.attendee
                
            except Ticket.DoesNotExist:
                raise serializers.ValidationError("Ticket no encontrado")
        
        return data


class CheckInLogSerializer(serializers.ModelSerializer):
    """Serializer para registros de check-in"""
    attendee_name = serializers.CharField(source='attendee.full_name', read_only=True)
    checked_by_name = serializers.CharField(source='checked_in_by.username', read_only=True)
    
    class Meta:
        model = CheckInLog
        fields = [
            'id', 'attendee', 'attendee_name', 'checked_in_by',
            'checked_by_name', 'checked_in_at', 'location',
            'device_info', 'notes'
        ]
        read_only_fields = ['checked_in_at']


class SurveyQuestionSerializer(serializers.ModelSerializer):
    """Serializer para preguntas de encuesta"""
    
    class Meta:
        model = SurveyQuestion
        fields = [
            'id', 'survey', 'question_text', 'question_type',
            'options', 'is_required', 'order'
        ]
    
    def validate_options(self, value):
        """Validar opciones según el tipo de pregunta"""
        question_type = self.initial_data.get('question_type')
        
        if question_type in ['multiple_choice', 'checkbox']:
            if not value or not isinstance(value, list):
                raise serializers.ValidationError(
                    "Debe proporcionar una lista de opciones para este tipo de pregunta"
                )
            if len(value) < 2:
                raise serializers.ValidationError(
                    "Debe proporcionar al menos 2 opciones"
                )
        
        return value


class SurveySerializer(serializers.ModelSerializer):
    """Serializer para encuestas"""
    event_title = serializers.CharField(source='event.title', read_only=True)
    questions = SurveyQuestionSerializer(many=True, read_only=True)
    is_available = serializers.ReadOnlyField()
    response_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Survey
        fields = [
            'id', 'event', 'event_title', 'title', 'description',
            'is_active', 'is_anonymous', 'allow_multiple_responses',
            'available_from', 'available_until', 'is_available',
            'questions', 'response_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_response_count(self, obj):
        """Cantidad de respuestas únicas"""
        return obj.responses.values('attendee').distinct().count()
    
    def validate(self, data):
        """Validaciones de la encuesta"""
        if 'available_from' in data and 'available_until' in data:
            if data['available_from'] >= data['available_until']:
                raise serializers.ValidationError(
                    "La fecha de inicio debe ser anterior a la fecha de fin"
                )
        
        return data


class SurveyResponseSerializer(serializers.ModelSerializer):
    """Serializer para respuestas de encuesta"""
    question_text = serializers.CharField(source='question.question_text', read_only=True)
    attendee_name = serializers.CharField(source='attendee.full_name', read_only=True)
    
    class Meta:
        model = SurveyResponse
        fields = [
            'id', 'survey', 'attendee', 'attendee_name',
            'question', 'question_text', 'answer', 'submitted_at'
        ]
        read_only_fields = ['submitted_at']
    
    def validate(self, data):
        """Validaciones de la respuesta"""
        survey = data['survey']
        question = data['question']
        
        # Verificar que la pregunta pertenece a la encuesta
        if question.survey != survey:
            raise serializers.ValidationError(
                "La pregunta no pertenece a esta encuesta"
            )
        
        # Verificar que la encuesta está disponible
        if not survey.is_available:
            raise serializers.ValidationError(
                "Esta encuesta no está disponible actualmente"
            )
        
        # Verificar respuestas múltiples
        if not survey.allow_multiple_responses:
            attendee = data.get('attendee')
            if attendee and SurveyResponse.objects.filter(
                survey=survey,
                attendee=attendee,
                question=question
            ).exists():
                raise serializers.ValidationError(
                    "Ya has respondido esta pregunta"
                )
        
        # Validar respuesta según tipo de pregunta
        answer = data['answer']
        if question.question_type == 'rating':
            try:
                rating = int(answer)
                if not 1 <= rating <= 5:
                    raise ValueError
            except ValueError:
                raise serializers.ValidationError(
                    "La calificación debe ser un número entre 1 y 5"
                )
        
        if question.question_type == 'yes_no':
            if answer.lower() not in ['yes', 'no', 'sí', 'si']:
                raise serializers.ValidationError(
                    "La respuesta debe ser 'Sí' o 'No'"
                )
        
        return data


class AttendeeStatisticsSerializer(serializers.Serializer):
    """Serializer para estadísticas de asistentes"""
    total_attendees = serializers.IntegerField()
    confirmed = serializers.IntegerField()
    pending = serializers.IntegerField()
    checked_in = serializers.IntegerField()
    cancelled = serializers.IntegerField()
    no_show = serializers.IntegerField()
    attendance_rate = serializers.FloatField()
    companies_represented = serializers.IntegerField()