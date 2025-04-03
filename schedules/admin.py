from django.contrib import admin
from .models import Schedule, ScheduleException, TimeSlot, AvailabilityPreference


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('id', 'doctor', 'clinic', 'get_day_name', 'start_time', 'end_time', 'is_active')
    list_filter = ('is_active', 'day_of_week', 'doctor', 'clinic')
    search_fields = ('doctor__first_name', 'doctor__last_name', 'clinic__name')

    fieldsets = (
        ('Basic Information', {
            'fields': ('doctor', 'clinic', 'day_of_week', 'is_active')
        }),
        ('Schedule Details', {
            'fields': ('start_time', 'end_time', 'break_start_time', 'break_end_time')
        }),
        ('Appointment Settings', {
            'fields': ('max_appointments', 'appointment_duration', 'buffer_time')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')

    def get_day_name(self, obj):
        return obj.get_day_of_week_display()

    get_day_name.short_description = 'Day'
    get_day_name.admin_order_field = 'day_of_week'


@admin.register(ScheduleException)
class ScheduleExceptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'doctor', 'clinic', 'start_date', 'end_date', 'exception_type', 'is_recurring')
    list_filter = ('exception_type', 'is_recurring', 'doctor', 'clinic')
    search_fields = ('doctor__first_name', 'doctor__last_name', 'clinic__name', 'reason')
    date_hierarchy = 'start_date'

    fieldsets = (
        ('Basic Information', {
            'fields': ('doctor', 'clinic', 'exception_type')
        }),
        ('Date and Time', {
            'fields': ('start_date', 'end_date', 'start_time', 'end_time')
        }),
        ('Exception Details', {
            'fields': ('reason', 'is_recurring', 'recurring_until')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ('id', 'doctor', 'clinic', 'date', 'start_time', 'end_time', 'is_available', 'is_booked')
    list_filter = ('is_available', 'is_booked', 'doctor', 'clinic', 'date')
    search_fields = ('doctor__first_name', 'doctor__last_name', 'clinic__name')
    date_hierarchy = 'date'

    fieldsets = (
        ('Basic Information', {
            'fields': ('doctor', 'clinic', 'date')
        }),
        ('Time Slot Details', {
            'fields': ('start_time', 'end_time', 'is_available', 'is_booked')
        }),
        ('Appointment', {
            'fields': ('appointment',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(AvailabilityPreference)
class AvailabilityPreferenceAdmin(admin.ModelAdmin):
    list_display = ('id', 'doctor', 'preferred_appointment_duration', 'max_appointments_per_day')
    list_filter = ('doctor',)
    search_fields = ('doctor__first_name', 'doctor__last_name')

    fieldsets = (
        ('Basic Information', {
            'fields': ('doctor',)
        }),
        ('Working Preferences', {
            'fields': ('preferred_working_days', 'preferred_start_time', 'preferred_end_time')
        }),
        ('Appointment Preferences', {
            'fields': ('preferred_appointment_duration', 'preferred_buffer_time', 'max_appointments_per_day',
                       'max_consecutive_days')
        }),
        ('Break Time', {
            'fields': ('preferred_break_start_time', 'preferred_break_end_time')
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')