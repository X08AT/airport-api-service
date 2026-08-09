import django_filters

from airport.models import Flight


class FlightFilter(django_filters.FilterSet):
    departure_after = django_filters.DateFilter(
        field_name="departure_time",
        lookup_expr="gte",
    )
    arrival_before = django_filters.DateFilter(
        field_name="arrival_time",
        lookup_expr="lte",
    )

    class Meta:
        model = Flight
        fields = ("status", "route", "airplane")
