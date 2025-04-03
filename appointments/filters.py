import django_filters
from django.db.models import Q
from django.utils import timezone
from .models import Appointment


class AppointmentFilter(django_filters.FilterSet):
    """
    Filter for Appointment queryset.
    """
    patient_name = django_filters.CharFilter(method='filter_patient_name')
    doctor_name = django_filters.CharFilter(method='filter_doctor_name')
    clinic_name = django_filters.CharFilter(field_name='clinic__name', lookup_expr='icontains')
    start_date = django_filters.DateFilter(field_name='scheduled_date', lookup_expr='gte')
    end_date = django_filters.DateFilter(field_name='scheduled_date', lookup_expr='lte')
    status = django_filters.MultipleChoiceFilter(choices=Appointment.AppointmentStatus.choices)
    appointment_type = django_filters.ChoiceFilter(choices=Appointment.AppointmentType.choices)
    is_today = django_filters.BooleanFilter(method='filter_is_today')
    is_past = django_filters.BooleanFilter(method='filter_is_past')
    is_upcoming = django_filters.BooleanFilter(method='filter_is_upcoming')
    is_first_visit = django_filters.BooleanFilter()
    is_follow_up = django_filters.BooleanFilter()
    is_emergency = django_filters.BooleanFilter()

    class Meta:
        model = Appointment
        fields = [
            'patient', 'doctor', 'clinic', 'patient_name', 'doctor_name',
            'clinic_name', 'start_date', 'end_date', 'status', 'appointment_type',
            'is_today', 'is_past', 'is_upcoming', 'is_first_visit',
            'is_follow_up', 'is_emergency', 'scheduled_date'
        ]

    def filter_patient_name(self, queryset, name, value):
        """
        Filter by patient's first or last name.
        """
        if not value:
            return queryset

        terms = value.split()

        if len(terms) == 1:
            # Single term, search in both first and last name
            return queryset.filter(
                Q(patient__first_name__icontains=terms[0]) |
                Q(patient__last_name__icontains=terms[0])
            )
        else:
            # Multiple terms, try different combinations
            queries = []
            for i in range(len(terms)):
                first_name_terms = ' '.join(terms[:i + 1])
                last_name_terms = ' '.join(terms[i + 1:])
                if first_name_terms and last_name_terms:
                    queries.append(
                        Q(patient__first_name__icontains=first_name_terms) &
                        Q(patient__last_name__icontains=last_name_terms)
                    )

            if queries:
                query = queries[0]
                for q in queries[1:]:
                    query |= q
                return queryset.filter(query)

            return queryset

    def filter_doctor_name(self, queryset, name, value):
        """
        Filter by doctor's first or last name.
        """
        if not value:
            return queryset

        terms = value.split()

        if len(terms) == 1:
            # Single term, search in both first and last name
            return queryset.filter(
                Q(doctor__first_name__icontains=terms[0]) |
                Q(doctor__last_name__icontains=terms[0])
            )
        else:
            # Multiple terms, try different combinations
            queries = []
            for i in range(len(terms)):
                first_name_terms = ' '.join(terms[:i + 1])
                last_name_terms = ' '.join(terms[i + 1:])
                if first_name_terms and last_name_terms:
                    queries.append(
                        Q(doctor__first_name__icontains=first_name_terms) &
                        Q(doctor__last_name__icontains=last_name_terms)
                    )

            if queries:
                query = queries[0]
                for q in queries[1:]:
                    query |= q
                return queryset.filter(query)

            return queryset

    def filter_is_today(self, queryset, name, value):
        """
        Filter appointments scheduled for today.
        """
        today = timezone.now().date()

        if value:
            return queryset.filter(scheduled_date=today)
        else:
            return queryset.exclude(scheduled_date=today)

    def filter_is_past(self, queryset, name, value):
        """
        Filter past appointments.
        """
        today = timezone.now().date()
        now = timezone.now().time()

        if value:
            # Past appointments are either on past dates, or today but with a time that has passed
            past_date_appointments = queryset.filter(scheduled_date__lt=today)
            today_past_appointments = queryset.filter(
                scheduled_date=today,
                scheduled_time__lt=now
            )
            return past_date_appointments | today_past_appointments
        else:
            # Non-past appointments are either on future dates, or today with a time that hasn't passed
            future_date_appointments = queryset.filter(scheduled_date__gt=today)
            today_future_appointments = queryset.filter(
                scheduled_date=today,
                scheduled_time__gte=now
            )
            return future_date_appointments | today_future_appointments

    def filter_is_upcoming(self, queryset, name, value):
        """
        Filter upcoming appointments.
        """
        today = timezone.now().date()
        now = timezone.now().time()

        if value:
            # Upcoming appointments are either on future dates, or today with a time that hasn't passed
            future_date_appointments = queryset.filter(scheduled_date__gt=today)
            today_future_appointments = queryset.filter(
                scheduled_date=today,
                scheduled_time__gte=now
            )
            return future_date_appointments | today_future_appointments
        else:
            # Non-upcoming appointments are either on past dates, or today but with a time that has passed
            past_date_appointments = queryset.filter(scheduled_date__lt=today)
            today_past_appointments = queryset.filter(
                scheduled_date=today,
                scheduled_time__lt=now
            )
            return past_date_appointments | today_past_appointments