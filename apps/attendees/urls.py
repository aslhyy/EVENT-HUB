from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AttendeeViewSet, CheckInLogViewSet,
    SurveyViewSet, SurveyResponseViewSet
)

router = DefaultRouter()
router.register(r'attendees', AttendeeViewSet, basename='attendee')
router.register(r'checkin-logs', CheckInLogViewSet, basename='checkinlog')
router.register(r'surveys', SurveyViewSet, basename='survey')
router.register(r'survey-responses', SurveyResponseViewSet, basename='surveyresponse')

urlpatterns = [
    path('', include(router.urls)),
]