import django_filters
from django.db.models import Q
from .models import Doctor


class DoctorFilter(django_filters.FilterSet):
    """
    Filter for Doctor queryset.
    """
    name = django_filters.CharFilter(method='filter_name')
    specialization = django_filters.CharFilter(field_name='specializations__name', lookup_expr='icontains')
    min_years_experience = django_filters.NumberFilter(field_name='years_of_experience', lookup_expr='gte')
    max_years_experience = django_filters.NumberFilter(field_name='years_of_experience', lookup_expr='lte')
    min_rating = django_filters.NumberFilter(field_name='avg_rating', lookup_expr='gte')
    max_fee = django_filters.NumberFilter(field_name='consultation_fee', lookup_expr='lte')
    min_fee = django_filters.NumberFilter(field_name='consultation_fee', lookup_expr='gte')
    accepts_insurance = django_filters.BooleanFilter()
    insurance_provider = django_filters.CharFilter(field_name='accepted_insurances__insurance__name',
                                                   lookup_expr='icontains')
    video_consultation = django_filters.BooleanFilter()
    home_visit = django_filters.BooleanFilter()
    languages = django_filters.CharFilter(method='filter_languages')
    status = django_filters.ChoiceFilter(choices=Doctor.Status.choices)

    class Meta:
        model = Doctor
        fields = [
            'name', 'specialization', 'min_years_experience', 'max_years_experience',
            'min_rating', 'max_fee', 'min_fee', 'accepts_insurance',
            'insurance_provider', 'video_consultation', 'home_visit',
            'languages', 'status'
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

    def filter_languages(self, queryset, name, value):
        """
        Filter by languages spoken.
        """
        if not value:
            return queryset

        # Split the input by commas and strip whitespace
        languages = [lang.strip().lower() for lang in value.split(',')]

        # Build query to match doctors who speak any of the requested languages
        query = Q()
        for language in languages:
            # Use regex to match the language as a whole word
            # This avoids partial matches like "eng" matching "bengali"
            query |= Q(languages__iregex=r'(^|[,\s]+){}($|[,\s]+)'.format(language))

        return queryset.filter(query)