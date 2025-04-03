import django_filters
from django.db.models import Q
from .models import Clinic


class ClinicFilter(django_filters.FilterSet):
    """
    Filter for Clinic queryset.
    """
    name = django_filters.CharFilter(lookup_expr='icontains')
    city = django_filters.CharFilter(lookup_expr='icontains')
    state = django_filters.CharFilter(lookup_expr='icontains')
    postal_code = django_filters.CharFilter(lookup_expr='icontains')
    clinic_type = django_filters.ChoiceFilter(choices=Clinic.ClinicType.choices)
    specialty = django_filters.CharFilter(field_name='specialties__name', lookup_expr='icontains')
    doctor = django_filters.CharFilter(method='filter_doctor')
    has_doctor = django_filters.BooleanFilter(method='filter_has_doctor')
    insurance = django_filters.CharFilter(field_name='accepted_insurances__insurance__name', lookup_expr='icontains')
    is_active = django_filters.BooleanFilter()

    class Meta:
        model = Clinic
        fields = [
            'name', 'city', 'state', 'postal_code', 'clinic_type',
            'specialty', 'doctor', 'has_doctor', 'insurance', 'is_active'
        ]

    def filter_doctor(self, queryset, name, value):
        """
        Filter clinics by doctor name.
        """
        if not value:
            return queryset

        # Break input into terms
        terms = value.split()

        # Create query to search in both first and last name
        query = Q()
        for term in terms:
            query |= Q(doctors__doctor__first_name__icontains=term) | Q(doctors__doctor__last_name__icontains=term)

        return queryset.filter(query).distinct()

    def filter_has_doctor(self, queryset, name, value):
        """
        Filter clinics by whether they have associated doctors.
        """
        if value is None:
            return queryset

        if value:
            return queryset.filter(doctors__isnull=False).distinct()
        else:
            return queryset.filter(doctors__isnull=True)