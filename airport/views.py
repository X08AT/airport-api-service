from django.db.models import Prefetch
from rest_framework import viewsets

from airport.models import (
    AirplaneType,
    Airplane,
    Crew,
    Country,
    City,
    Airport,
    Route,
    Flight,
    Order,
    Ticket
)
from airport.serializers import (
    AirplaneTypeSerializer,
    AirplaneSerializer,
    AirplaneListSerializer,
    AirplaneDetailSerializer,
    CrewSerializer,
    CrewListSerializer,
    CountrySerializer,
    CitySerializer,
    CityListSerializer,
    CityDetailSerializer,
    AirportSerializer,
    AirportListSerializer,
    AirportDetailSerializer,
    RouteSerializer,
    RouteListSerializer,
    RouteDetailSerializer,
    FlightSerializer,
    FlightListSerializer,
    FlightDetailSerializer,
    OrderSerializer,
    OrderListSerializer,
    OrderDetailSerializer
)


class AirplaneTypeViewSet(viewsets.ModelViewSet):
    queryset = AirplaneType.objects.all()
    serializer_class = AirplaneTypeSerializer


class AirplaneViewSet(viewsets.ModelViewSet):
    queryset = Airplane.objects.all()
    serializer_class = AirplaneSerializer

    def get_queryset(self):
        airplane_type = self.request.query_params.get("airplane_type")

        queryset = Airplane.objects.all()

        if airplane_type:
            airplane_type_ids = [
                int(airplane_type_id)
                for airplane_type_id in airplane_type.split(",")
            ]
            queryset = queryset.filter(airplane_type_id__in=airplane_type_ids)

        if self.action in ("list", "retrieve"):
            return queryset.select_related("airplane_type")

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return AirplaneListSerializer
        if self.action == "retrieve":
            return AirplaneDetailSerializer

        return AirplaneSerializer


class CrewViewSet(viewsets.ModelViewSet):
    queryset = Crew.objects.all()
    serializer_class = CrewSerializer

    def get_queryset(self):
        position = self.request.query_params.get("position")

        queryset = Crew.objects.all()

        if position:
            queryset = queryset.filter(position=position)

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return CrewListSerializer

        return CrewSerializer


class CountryViewSet(viewsets.ModelViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer


class CityViewSet(viewsets.ModelViewSet):
    queryset = City.objects.all()
    serializer_class = CitySerializer

    def get_queryset(self):
        country = self.request.query_params.get("country")

        queryset = City.objects.all()

        if country:
            country_ids = [
                int(country_id) for country_id in country.split(",")
            ]
            queryset = queryset.filter(country_id__in=country_ids)

        if self.action in ("list", "retrieve"):
            return queryset.select_related("country")

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return CityListSerializer
        if self.action == "retrieve":
            return CityDetailSerializer

        return CitySerializer


class AirportViewSet(viewsets.ModelViewSet):
    queryset = Airport.objects.all()
    serializer_class = AirportSerializer

    def get_queryset(self):
        city = self.request.query_params.get("city")

        queryset = Airport.objects.all()

        if city:
            city_ids = [int(city_id) for city_id in city.split(",")]
            queryset = queryset.filter(city_id__in=city_ids)

        if self.action in ("list", "retrieve"):
            return queryset.select_related("city", "city__country")

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return AirportListSerializer
        if self.action == "retrieve":
            return AirportDetailSerializer

        return AirportSerializer


class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer

    def get_queryset(self):
        source = self.request.query_params.get("source")
        destination = self.request.query_params.get("destination")

        queryset = Route.objects.all()

        if source:
            source_ids = [int(source_id) for source_id in source.split(",")]
            queryset = queryset.filter(source_id__in=source_ids)

        if destination:
            destination_ids = [
                int(destination_id)
                for destination_id in destination.split(",")
            ]
            queryset = queryset.filter(destination_id__in=destination_ids)

        if self.action in ("list", "retrieve"):
            return queryset.select_related(
                "source__city__country",
                "destination__city__country"
            )

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return RouteListSerializer
        if self.action == "retrieve":
            return RouteDetailSerializer

        return RouteSerializer


class FlightViewSet(viewsets.ModelViewSet):
    queryset = Flight.objects.all()
    serializer_class = FlightSerializer

    def get_queryset(self):
        status = self.request.query_params.get("status")
        route = self.request.query_params.get("route")
        airplane = self.request.query_params.get("airplane")

        queryset = Flight.objects.all()

        if status:
            queryset = queryset.filter(status=status)

        if route:
            route_ids = [int(route_id) for route_id in route.split(",")]
            queryset = queryset.filter(route_id__in=route_ids)

        if airplane:
            airplane_ids = [
                int(airplane_id) for airplane_id in airplane.split(",")
            ]
            queryset = queryset.filter(airplane_id__in=airplane_ids)

        if self.action in ("list", "retrieve"):
            queryset = queryset.select_related(
                "route__source__city__country",
                "route__destination__city__country",
                "airplane__airplane_type"
            ).prefetch_related("crew")

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return FlightListSerializer
        if self.action == "retrieve":
            return FlightDetailSerializer

        return FlightSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def get_queryset(self):
        queryset = Order.objects.filter(user=self.request.user)

        if self.action in ("list", "retrieve"):
            queryset = queryset.prefetch_related(
                Prefetch(
                    "tickets",
                    queryset=Ticket.objects.select_related(
                        "flight__route__source__city__country",
                        "flight__route__destination__city__country",
                        "flight__airplane__airplane_type",
                    )
                )
            )

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        if self.action == "retrieve":
            return OrderDetailSerializer

        return OrderSerializer
