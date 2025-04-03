from django.contrib import admin
from .models import (
    Appointment, AppointmentDocument, MedicalRecord,
    AppointmentReminder, AppointmentFeedback
)


class AppointmentDocumentInline(admin.TabularInline):
    model = AppointmentDocument
    extra = 1


class MedicalRecordInline(admin.StackedInline):
    model = MedicalRecord
    extra = 0
    can_delete = False


class AppointmentReminderInline(admin.TabularInline):
    model = AppointmentReminder
    extra = 0
    readonly_fields = ['sent_at', 'status', 'error_message']


class AppointmentFeedbackInline(admin.StackedInline):
    model = AppointmentFeedback
    extra = 0
    can_delete = False


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'doctor', 'clinic', 'appointment_type',
                    'status', 'scheduled_date', 'scheduled_time', 'is_first_visit', 'is_emergency')
    list_filter = ('status', 'appointment_type', 'scheduled_date', 'is_first_visit',
                   'is_follow_up', 'is_emergency', 'insurance_verified')
    search_fields = ('patient__first_name', 'patient__last_name',
                     'doctor__first_name', 'doctor__last_name',
                     'clinic__name', 'reason', 'chief_complaint')
    date_hierarchy = 'scheduled_date'
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('patient', 'doctor', 'clinic', 'appointment_type')
        }),
        ('Scheduling', {
            'fields': ('scheduled_date', 'scheduled_time', 'duration', 'status')
        }),
        ('Details', {
            'fields': ('reason', 'notes', 'chief_complaint', 'is_first_visit',
                       'is_follow_up', 'is_emergency', 'followup_date')
        }),
        ('Cancellation Information', {
            'fields': ('cancellation_reason', 'cancelled_by', 'cancelled_at'),
            'classes': ('collapse',)
        }),
        ('Payment and Insurance', {
            'fields': ('insurance_verified', 'payment_status'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'reminder_sent'),
            'classes': ('collapse',)
        }),
    )
    inlines = [
        AppointmentDocumentInline,
        MedicalRecordInline,
        AppointmentReminderInline,
        AppointmentFeedbackInline
    ]


@admin.register(AppointmentDocument)
class AppointmentDocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'appointment', 'title', 'document_type', 'uploaded_by', 'created_at')
    list_filter = ('document_type', 'created_at')
    search_fields = ('title', 'notes', 'appointment__patient__first_name',
                     'appointment__patient__last_name', 'appointment__doctor__first_name',
                     'appointment__doctor__last_name')
    readonly_fields = ['created_at', 'updated_at']


@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'appointment', 'get_patient_name', 'get_doctor_name', 'doctor_signature', 'created_at')
    list_filter = ('doctor_signature', 'created_at')
    search_fields = ('appointment__patient__first_name', 'appointment__patient__last_name',
                     'appointment__doctor__first_name', 'appointment__doctor__last_name',
                     'symptoms', 'diagnosis', 'treatment_plan')
    readonly_fields = ['created_at', 'updated_at']

    def get_patient_name(self, obj):
        return f"{obj.appointment.patient.first_name} {obj.appointment.patient.last_name}"

    get_patient_name.short_description = 'Patient'

    def get_doctor_name(self, obj):
        return f"{obj.appointment.doctor.first_name} {obj.appointment.doctor.last_name}"

    get_doctor_name.short_description = 'Doctor'


@admin.register(AppointmentReminder)
class AppointmentReminderAdmin(admin.ModelAdmin):
    list_display = ('id', 'appointment', 'reminder_type', 'scheduled_time',
                    'status', 'sent_at')
    list_filter = ('reminder_type', 'status', 'scheduled_time')
    search_fields = ('appointment__patient__first_name', 'appointment__patient__last_name')
    readonly_fields = ['created_at', 'updated_at', 'sent_at', 'status', 'error_message']


@admin.register(AppointmentFeedback)
class AppointmentFeedbackAdmin(admin.ModelAdmin):
    list_display = ('id', 'appointment', 'rating', 'doctor_punctuality',
                    'facility_cleanliness', 'would_recommend', 'created_at')
    list_filter = ('rating', 'doctor_punctuality', 'facility_cleanliness',
                   'staff_friendliness', 'would_recommend', 'created_at')
    search_fields = ('appointment__patient__first_name', 'appointment__patient__last_name',
                     'appointment__doctor__first_name', 'appointment__doctor__last_name',
                     'comments')
    readonly_fields = ['created_at', 'updated_at']