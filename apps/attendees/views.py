from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Count, Q

from .models import Attendee, CheckInLog, Survey, SurveyQuestion, SurveyResponse
from .serializers import (
    AttendeeListSerializer, AttendeeDetailSerializer, CheckInSerializer,
    CheckInLogSerializer, SurveySerializer, SurveyQuestionSerializer,
    SurveyResponseSerializer, AttendeeStatisticsSerializer
)
from .filters import AttendeeFilter
from config.permissions import CanCheckIn, CanManageSurvey


class AttendeeViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar asistentes
    
    list: Listar asistentes
    retrieve: Obtener detalle de un asistente
    create: Registrar nuevo asistente
    update: Actualizar asistente
    destroy: Eliminar asistente
    """
    queryset = Attendee.objects.all().select_related(
        'user', 'event', 'event__venue'
    )
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AttendeeFilter
    search_fields = ['first_name', 'last_name', 'email', 'company']
    ordering_fields = ['registration_date', 'last_name']
    ordering = ['-registration_date']
    
    def get_serializer_class(self):
        """Usar serializer diferente según la acción"""
        if self.action == 'list':
            return AttendeeListSerializer
        elif self.action == 'checkin':
            return CheckInSerializer
        elif self.action == 'statistics':
            return AttendeeStatisticsSerializer
        return AttendeeDetailSerializer
    
    def get_queryset(self):
        """Personalizar queryset según el usuario"""
        user = self.request.user
        
        if user.is_staff:
            return self.queryset
        
        # Organizadores ven asistentes de sus eventos
        from apps.events.models import Event
        my_events = Event.objects.filter(organizer=user)
        
        return self.queryset.filter(
            Q(user=user) | Q(event__in=my_events)
        )
    
    @action(detail=False, methods=['post'])
    @transaction.atomic
    def checkin(self, request):
        """
        Endpoint personalizado: Realizar check-in de asistente
        POST /api/attendees/checkin/
        Body: {
            "attendee_id": 1,
            "location": "Puerta Principal",
            "notes": "Check-in exitoso"
        }
        O usando ticket_code:
        Body: {
            "ticket_code": "uuid-here",
            "location": "Puerta Principal"
        }
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        attendee = serializer.validated_data['attendee']
        location = serializer.validated_data.get('location', '')
        notes = serializer.validated_data.get('notes', '')
        
        # Verificar permisos
        if not (request.user.is_staff or attendee.event.organizer == request.user):
            return Response(
                {'error': 'No tiene permisos para realizar check-in'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Realizar check-in
        attendee.status = 'checked_in'
        attendee.checked_in_at = timezone.now()
        attendee.checked_in_by = request.user
        attendee.save()
        
        # Registrar en log
        CheckInLog.objects.create(
            attendee=attendee,
            checked_in_by=request.user,
            location=location,
            notes=notes
        )
        
        # Marcar ticket como usado si existe
        if hasattr(attendee, 'ticket') and attendee.ticket:
            attendee.ticket.status = 'used'
            attendee.ticket.used_at = timezone.now()
            attendee.ticket.save()
        
        return Response({
            'success': True,
            'message': 'Check-in realizado exitosamente',
            'attendee': AttendeeDetailSerializer(attendee).data
        })
    
    @action(detail=False, methods=['get'])
    def my_registrations(self, request):
        """
        Endpoint personalizado: Mis registros a eventos
        GET /api/attendees/my_registrations/
        """
        attendees = Attendee.objects.filter(user=request.user)
        
        # Filtros opcionales
        upcoming = request.query_params.get('upcoming')
        if upcoming == 'true':
            now = timezone.now()
            attendees = attendees.filter(event__start_date__gte=now)
        
        serializer = AttendeeListSerializer(attendees, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """
        Endpoint personalizado: Confirmar asistencia
        POST /api/attendees/{id}/confirm/
        """
        attendee = self.get_object()
        
        if attendee.user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'No tiene permisos para confirmar esta asistencia'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        attendee.status = 'confirmed'
        attendee.confirmation_date = timezone.now()
        attendee.save()
        
        # Enviar email de confirmación
        self._send_confirmation_email(attendee)
        
        return Response({
            'success': True,
            'message': 'Asistencia confirmada',
            'attendee': AttendeeDetailSerializer(attendee).data
        })
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Endpoint personalizado: Cancelar asistencia
        POST /api/attendees/{id}/cancel/
        """
        attendee = self.get_object()
        
        if attendee.user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'No tiene permisos para cancelar esta asistencia'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        attendee.status = 'cancelled'
        attendee.save()
        
        return Response({
            'success': True,
            'message': 'Asistencia cancelada'
        })
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Endpoint personalizado: Estadísticas de asistentes
        GET /api/attendees/statistics/?event_id=1
        """
        event_id = request.query_params.get('event_id')
        
        if not event_id:
            return Response(
                {'error': 'Debe proporcionar event_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = Attendee.objects.filter(event_id=event_id)
        
        stats = {
            'total_attendees': queryset.count(),
            'confirmed': queryset.filter(status='confirmed').count(),
            'pending': queryset.filter(status='pending').count(),
            'checked_in': queryset.filter(status='checked_in').count(),
            'cancelled': queryset.filter(status='cancelled').count(),
            'no_show': queryset.filter(status='no_show').count(),
            'attendance_rate': 0,
            'companies_represented': queryset.exclude(
                company=''
            ).values('company').distinct().count(),
        }
        
        # Calcular tasa de asistencia
        confirmed = stats['confirmed'] + stats['checked_in']
        if confirmed > 0:
            stats['attendance_rate'] = round(
                (stats['checked_in'] / confirmed) * 100, 2
            )
        
        serializer = AttendeeStatisticsSerializer(stats)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def export(self, request):
        """
        Endpoint personalizado: Exportar lista de asistentes
        GET /api/attendees/export/?event_id=1&format=csv
        """
        event_id = request.query_params.get('event_id')
        
        if not event_id:
            return Response(
                {'error': 'Debe proporcionar event_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar permisos
        from apps.events.models import Event
        event = Event.objects.get(id=event_id)
        
        if event.organizer != request.user and not request.user.is_staff:
            return Response(
                {'error': 'No tiene permisos para exportar esta lista'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        attendees = Attendee.objects.filter(event_id=event_id)
        
        # Formato simple (puede mejorarse con CSV real)
        data = []
        for attendee in attendees:
            data.append({
                'full_name': attendee.full_name,
                'email': attendee.email,
                'phone': attendee.phone,
                'company': attendee.company,
                'status': attendee.status,
                'registration_date': attendee.registration_date,
            })
        
        return Response(data)
    
    def _send_confirmation_email(self, attendee):
        """Enviar email de confirmación de asistencia"""
        event = attendee.event
        
        subject = f'Confirmación de asistencia - {event.title}'
        message = f"""
        Hola {attendee.first_name},
        
        Tu asistencia al evento "{event.title}" ha sido confirmada.
        
        Detalles del evento:
        - Fecha: {event.start_date.strftime('%Y-%m-%d %H:%M')}
        - Lugar: {event.venue.name}
        - Dirección: {event.venue.address}
        
        ¡Te esperamos!
        """
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [attendee.email],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Error enviando email: {e}")


class CheckInLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para ver registros de check-in
    
    list: Listar registros de check-in
    retrieve: Obtener detalle de un registro
    """
    queryset = CheckInLog.objects.all().select_related(
        'attendee', 'checked_in_by'
    )
    serializer_class = CheckInLogSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ['checked_in_at']
    ordering = ['-checked_in_at']


class SurveyViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar encuestas
    
    list: Listar encuestas
    retrieve: Obtener detalle de una encuesta
    create: Crear nueva encuesta
    update: Actualizar encuesta
    destroy: Eliminar encuesta
    """
    queryset = Survey.objects.all().select_related('event')
    serializer_class = SurveySerializer
    permission_classes = [CanManageSurvey]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['title', 'description']
    
    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        """
        Endpoint personalizado: Resultados de la encuesta
        GET /api/surveys/{id}/results/
        """
        survey = self.get_object()
        
        questions = survey.questions.all()
        results = []
        
        for question in questions:
            question_data = {
                'question': question.question_text,
                'type': question.question_type,
                'total_responses': question.responses.count(),
            }
            
            # Agregaciones según tipo de pregunta
            if question.question_type == 'rating':
                responses = question.responses.all()
                ratings = [int(r.answer) for r in responses if r.answer.isdigit()]
                
                if ratings:
                    question_data['average_rating'] = sum(ratings) / len(ratings)
                    question_data['rating_distribution'] = {
                        str(i): ratings.count(i) for i in range(1, 6)
                    }
            
            elif question.question_type in ['multiple_choice', 'yes_no']:
                responses = question.responses.values('answer').annotate(
                    count=Count('answer')
                )
                question_data['answers'] = list(responses)
            
            results.append(question_data)
        
        return Response({
            'survey': survey.title,
            'total_responses': survey.responses.values('attendee').distinct().count(),
            'results': results
        })


class SurveyResponseViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar respuestas de encuestas
    
    list: Listar respuestas
    create: Crear nueva respuesta
    """
    queryset = SurveyResponse.objects.all().select_related(
        'survey', 'attendee', 'question'
    )
    serializer_class = SurveyResponseSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    
    @action(detail=False, methods=['post'])
    @transaction.atomic
    def submit_survey(self, request):
        """
        Endpoint personalizado: Enviar respuestas completas de encuesta
        POST /api/survey-responses/submit_survey/
        Body: {
            "survey_id": 1,
            "attendee_id": 1,
            "responses": [
                {"question_id": 1, "answer": "Excelente"},
                {"question_id": 2, "answer": "5"}
            ]
        }
        """
        survey_id = request.data.get('survey_id')
        attendee_id = request.data.get('attendee_id')
        responses_data = request.data.get('responses', [])
        
        if not survey_id or not responses_data:
            return Response(
                {'error': 'Debe proporcionar survey_id y responses'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        survey = Survey.objects.get(id=survey_id)
        attendee = Attendee.objects.get(id=attendee_id) if attendee_id else None
        
        # Verificar que la encuesta está disponible
        if not survey.is_available:
            return Response(
                {'error': 'Esta encuesta no está disponible actualmente'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Crear respuestas
        created_responses = []
        for resp_data in responses_data:
            question = SurveyQuestion.objects.get(id=resp_data['question_id'])
            
            response = SurveyResponse.objects.create(
                survey=survey,
                attendee=attendee,
                question=question,
                answer=resp_data['answer']
            )
            created_responses.append(response)
        
        return Response({
            'success': True,
            'message': f'{len(created_responses)} respuestas guardadas',
            'responses': SurveyResponseSerializer(created_responses, many=True).data
        }, status=status.HTTP_201_CREATED)