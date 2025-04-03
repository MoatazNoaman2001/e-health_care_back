import django_filters
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from .models import Patient


class PatientFilter(django_filters.FilterSet):
    """
    Filter for Patient queryset.
    """
    name = django_filters.CharFilter(method='filter_name')
    min_age = django_filters.NumberFilter(method='filter_min_age')
    max_age = django_filters.NumberFilter(method='filter_max_age')
    gender = django_filters.ChoiceFilter(choices=Patient.Gender.choices)
    blood_type = django_filters.ChoiceFilter(choices=Patient.BloodType.choices)
    is_insured = django_filters.BooleanFilter()
    has_allergies = django_filters.BooleanFilter(method='filter_has_allergies')
    created_after = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = Patient
        fields = [
            'name', 'gender', 'blood_type', 'is_insured',
            'has_allergies', 'min_age', 'max_age',
            'created_after', 'created_before'
        ]

    def filter_name(self, queryset, name, value):
        """
        Filter by first name or last name.
        """
        if not value:
            return queryset

        terms = value.split()

        if len(terms) == 1:
            # Single term, search in both first and last name
            return queryset.filter(
                Q(first_name__icontains=terms[0]) |
                Q(last_name__icontains=terms[0])
            )
        else:
            # Multiple terms, try different combinations
            queries = []
            for i in range(len(terms)):
                first_name_terms = ' '.join(terms[:i + 1])
                last_name_terms = ' '.join(terms[i + 1:])
                if first_name_terms and last_name_terms:
                    queries.append(
                        Q(first_name__icontains=first_name_terms) &
                        Q(last_name__icontains=last_name_terms)
                    )

            if queries:
                query = queries[0]
                for q in queries[1:]:
                    query |= q
                return queryset.filter(query)

            return queryset

    def filter_min_age(self, queryset, name, value):
        """
        Filter patients by minimum age.
        """
        if not value:
            return queryset

        # Calculate the date of birth for someone who is 'value' years old
        max_date_of_birth = timezone.now().date() - timedelta(days=value * 365.25)

        return queryset.filter(date_of_birth__lte=max_date_of_birth)

    def filter_max_age(self, queryset, name, value):
        """
        Filter patients by maximum age.
        """
        if not value:
            return queryset

        # Calculate the date of birth for someone who is 'value' years old
        min_date_of_birth = timezone.now().date() - timedelta(days=value * 365.25)

        return queryset.filter(date_of_birth__gte=min_date_of_birth)

    def filter_has_allergies(self, queryset, name, value):
        """
        Filter patients by whether they have allergies.
        """
        if value is None:
            return queryset

        if value:
            return queryset.exclude(allergies__isnull=True).exclude(allergies='')
        else:
            return queryset.filter(Q(allergies__isnull=True) | Q(allergies=''))