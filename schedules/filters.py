import django_filters
from .models import Schedule, ScheduleException, TimeSlot


class ScheduleFilter(django_filters.FilterSet):
    """
    Filter for Schedule queryset.
    """
    doctor_id = django_filters.NumberFilter(field_name='doctor__id')
    clinic_id = django_filters.NumberFilter(field_name='clinic__id')
    day_of_week = django_filters.NumberFilter(field_name='day_of_week')
    is_active = django_filters.BooleanFilter(field_name='is_active')

    class Meta:
        model = Schedule
        fields = [
            'doctor', 'doctor_id', 'clinic', 'clinic_id',
            'day_of_week', 'is_active'
        ]


class ScheduleExceptionFilter(django_filters.FilterSet):
    """
    Filter for ScheduleException queryset.
    """
    doctor_id = django_filters.NumberFilter(field_name='doctor__id')
    clinic_id = django_filters.NumberFilter(field_name='clinic__id')
    start_date_after = django_filters.DateFilter(field_name='start_date', lookup_expr='gte')
    start_date_before = django_filters.DateFilter(field_name='start_date', lookup_expr='lte')
    end_date_after = django_filters.DateFilter(field_name='end_date', lookup_expr='gte')
    end_date_before = django_filters.DateFilter(field_name='end_date', lookup_expr='lte')
    exception_type = django_filters.ChoiceFilter(field_name='exception_type',
                                                 choices=ScheduleException.ExceptionType.choices)
    is_recurring = django_filters.BooleanFilter(field_name='is_recurring')

    class Meta:
        model = ScheduleException
        fields = [
            'doctor', 'doctor_id', 'clinic', 'clinic_id',
            'start_date_after', 'start_date_before',
            'end_date_after', 'end_date_before',
            'exception_type', 'is_recurring'
        ]


class TimeSlotFilter(django_filters.FilterSet):
    """
    Filter for TimeSlot queryset.
    """
    doctor_id = django_filters.NumberFilter(field_name='doctor__id')
    clinic_id = django_filters.NumberFilter(field_name='clinic__id')
    date_after = django_filters.DateFilter(field_name='date', lookup_expr='gte')
    date_before = django_filters.DateFilter(field_name='date', lookup_expr='lte')
    start_time_after = django_filters.TimeFilter(field_name='start_time', lookup_expr='gte')
    start_time_before = django_filters.TimeFilter(field_name='start_time', lookup_expr='lte')
    is_available = django_filters.BooleanFilter(field_name='is_available')
    is_booked = django_filters.BooleanFilter(field_name='is_booked')

    class Meta:
        model = TimeSlot
        fields = [
            'doctor', 'doctor_id', 'clinic', 'clinic_id',
            'date', 'date_after', 'date_before',
            'start_time_after', 'start_time_before',
            'is_available', 'is_booked'
        ]