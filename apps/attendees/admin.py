from django.contrib import admin
from apps.attendees.models import Attendee, CheckInLog, Survey, SurveyQuestion, SurveyResponse


@admin.register(Attendee)
class AttendeeAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'event', 'status', 'registration_date']
    list_filter = ['status', 'event', 'registration_date']
    search_fields = ['first_name', 'last_name', 'email', 'company']
    date_hierarchy = 'registration_date'
    ordering = ['-registration_date']


@admin.register(CheckInLog)
class CheckInLogAdmin(admin.ModelAdmin):
    list_display = ['attendee', 'checked_in_at', 'checked_in_by', 'location']
    list_filter = ['checked_in_at']
    search_fields = ['attendee__first_name', 'attendee__last_name']
    date_hierarchy = 'checked_in_at'


@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = ['title', 'event', 'is_active', 'is_anonymous', 'created_at']
    list_filter = ['is_active', 'is_anonymous', 'event']
    search_fields = ['title', 'description']