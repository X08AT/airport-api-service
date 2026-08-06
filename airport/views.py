from django.db.models import Prefetch, Count, F
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated

from airport.filters import FlightFilter
from airport.mixins import ImageUploadMixin
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
from airport.permissions import IsAdminOrIfAuthenticatedReadOnly
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
    OrderDetailSerializer,
    AirplaneImageSerializer,
    CountryImageSerializer,
    CountryListAndRetrieveSerializer,
    CityImageSerializer,
    AirportImageSerializer
)


@extend_schema_view(
    list=extend_schema(summary="List of airplane types"),
    retrieve=extend_schema(summary="Retrieve airplane type"),
    create=extend_schema(summary="Create airplane type"),
    update=extend_schema(summary="Update airplane type"),
    partial_update=extend_schema(summary="Partially update airplane type"),
    destroy=extend_schema(summary="Delete airplane type"),
)
@extend_schema(tags=["Airplane Types"])
class AirplaneTypeViewSet(viewsets.ModelViewSet):
    queryset = AirplaneType.objects.all()
    serializer_class = AirplaneTypeSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    filter_backends = (
        SearchFilter,
        OrderingFilter,
    )

    search_fields = ("name",)
    ordering_fields = ("name",)


@extend_schema_view(
    list=extend_schema(
        summary="List of airplanes",
        description=(
            "Supports filtering by airplane type, searching by registration "
            "number, and ordering by registration number."
        ),
    ),
    retrieve=extend_schema(summary="Retrieve airplane"),
    create=extend_schema(summary="Create airplane"),
    update=extend_schema(summary="Update airplane"),
    partial_update=extend_schema(summary="Partially update airplane"),
    destroy=extend_schema(summary="Delete airplane"),
)
@extend_schema(tags=["Airplanes"])
class AirplaneViewSet(ImageUploadMixin, viewsets.ModelViewSet):
    queryset = Airplane.objects.all()
    serializer_class = AirplaneSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    filter_backends = (
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
    )
    filterset_fields = ("airplane_type",)
    search_fields = ("registration_number",)
    ordering_fields = ("registration_number",)

    def get_queryset(self):
        queryset = self.queryset

        if self.action in ("list", "retrieve"):
            return queryset.select_related("airplane_type")

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return AirplaneListSerializer
        if self.action == "retrieve":
            return AirplaneDetailSerializer
        if self.action == "upload_image":
            return AirplaneImageSerializer

        return AirplaneSerializer

    @extend_schema(
        summary="Upload airplane image",
        description="Upload or replace an image for airplane.",
        request=AirplaneImageSerializer,
        responses=AirplaneImageSerializer,
    )
    @action(
        methods=["post"],
        detail=True,
        url_path="upload-image",
        parser_classes=(MultiPartParser,)
    )
    def upload_image(self, request, pk=None):
        return super().upload_image(request, pk)


@extend_schema_view(
    list=extend_schema(summary="List of crew members"),
    retrieve=extend_schema(summary="Retrieve crew member"),
    create=extend_schema(summary="Create crew member"),
    update=extend_schema(summary="Update crew member"),
    partial_update=extend_schema(summary="Partially update crew member"),
    destroy=extend_schema(summary="Delete crew member"),
)
@extend_schema(tags=["Crews"])
class CrewViewSet(viewsets.ModelViewSet):
    queryset = Crew.objects.all()
    serializer_class = CrewSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    filter_backends = (
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
    )
    filterset_fields = ("position",)
    search_fields = ("first_name", "last_name",)
    ordering_fields = ("last_name", "first_name",)

    def get_serializer_class(self):
        if self.action == "list":
            return CrewListSerializer

        return CrewSerializer


@extend_schema_view(
    list=extend_schema(summary="List of countries"),
    retrieve=extend_schema(summary="Retrieve country"),
    create=extend_schema(summary="Create country"),
    update=extend_schema(summary="Update country"),
    partial_update=extend_schema(summary="Partially update country"),
    destroy=extend_schema(summary="Delete country"),
)
@extend_schema(tags=["Countries"])
class CountryViewSet(ImageUploadMixin, viewsets.ModelViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    filter_backends = (
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
    )
    search_fields = ("name",)
    ordering_fields = ("name",)

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return CountryListAndRetrieveSerializer
        if self.action == "upload_image":
            return CountryImageSerializer

        return CountrySerializer

    @extend_schema(
        summary="Upload country flag image",
        description="Upload or replace an flag image for country.",
        request=CountryImageSerializer,
        responses=CountryImageSerializer,
    )
    @action(
        methods=["post"],
        detail=True,
        url_path="upload-image",
        parser_classes=(MultiPartParser,)
    )
    def upload_image(self, request, pk=None):
        return super().upload_image(request, pk)


@extend_schema_view(
    list=extend_schema(
        summary="List of cities",
        description=(
            "Supports filtering by country, searching by city name, "
            "and ordering by city name."
        ),
    ),
    retrieve=extend_schema(summary="Retrieve city"),
    create=extend_schema(summary="Create city"),
    update=extend_schema(summary="Update city"),
    partial_update=extend_schema(summary="Partially update city"),
    destroy=extend_schema(summary="Delete city"),
)
@extend_schema(tags=["Cities"])
class CityViewSet(ImageUploadMixin, viewsets.ModelViewSet):
    queryset = City.objects.all()
    serializer_class = CitySerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    filter_backends = (
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
    )
    filterset_fields = ("country",)
    search_fields = ("name",)
    ordering_fields = ("name",)

    def get_queryset(self):
        queryset = self.queryset

        if self.action in ("list", "retrieve"):
            return queryset.select_related("country")

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return CityListSerializer
        if self.action == "retrieve":
            return CityDetailSerializer
        if self.action == "upload_image":
            return CityImageSerializer

        return CitySerializer

    @extend_schema(
        summary="Upload city image",
        description="Upload or replace an image for city.",
        request=CityImageSerializer,
        responses=CityImageSerializer,
    )
    @action(
        methods=["post"],
        detail=True,
        url_path="upload-image",
        parser_classes=(MultiPartParser,)
    )
    def upload_image(self, request, pk=None):
        return super().upload_image(request, pk)


@extend_schema_view(
    list=extend_schema(
        summary="List of airports",
        description=(
            "Supports filtering by city, searching by airport name, IATA code "
            "or city name, and ordering by airport name."
        ),
    ),
    retrieve=extend_schema(summary="Retrieve airport"),
    create=extend_schema(summary="Create airport"),
    update=extend_schema(summary="Update airport"),
    partial_update=extend_schema(summary="Partially update airport"),
    destroy=extend_schema(summary="Delete airport"),
)
@extend_schema(tags=["Airports"])
class AirportViewSet(ImageUploadMixin, viewsets.ModelViewSet):
    queryset = Airport.objects.all()
    serializer_class = AirportSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    filter_backends = (
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
    )
    filterset_fields = ("city",)
    search_fields = ("name", "iata_code", "city__name")
    ordering_fields = ("name",)

    def get_queryset(self):
        queryset = self.queryset

        if self.action in ("list", "retrieve"):
            return queryset.select_related("city", "city__country")

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return AirportListSerializer
        if self.action == "retrieve":
            return AirportDetailSerializer
        if self.action == "upload_image":
            return AirportImageSerializer

        return AirportSerializer

    @extend_schema(
        summary="Upload airport image",
        description="Upload or replace an image for airport.",
        request=AirportImageSerializer,
        responses=AirportImageSerializer,
    )
    @action(
        methods=["post"],
        detail=True,
        url_path="upload-image",
        parser_classes=(MultiPartParser,)
    )
    def upload_image(self, request, pk=None):
        return super().upload_image(request, pk)


@extend_schema_view(
    list=extend_schema(
        summary="List of routes",
        description=(
            "Supports filtering by source and destination airports, "
            "searching by airport IATA code or city name, "
            "and ordering by distance."
        ),
    ),
    retrieve=extend_schema(summary="Retrieve route"),
    create=extend_schema(summary="Create route"),
    update=extend_schema(summary="Update route"),
    partial_update=extend_schema(summary="Partially update route"),
    destroy=extend_schema(summary="Delete route"),
)
@extend_schema(tags=["Routes"])
class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    filter_backends = (
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
    )
    filterset_fields = ("source", "destination")
    search_fields = (
        "source__city__name",
        "destination__city__name",
        "source__iata_code",
        "destination__iata_code",
    )
    ordering_fields = ("distance",)

    def get_queryset(self):
        queryset = self.queryset

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


@extend_schema_view(
    list=extend_schema(
        summary="List of flights",
        description=(
            "Retrieve a list of flights. "
            "Supports filtering by departure date, "
            "route, crew, and airplane,"
            " searching by flight number and airport "
            "IATA codes, and ordering by departure or arrival time."
        ),
    ),
    retrieve=extend_schema(
        summary="Retrieve flight",
        description=(
            "Retrieve detailed flight information, including available seats."
        ),
    ),
    create=extend_schema(summary="Create flight"),
    update=extend_schema(summary="Update flight"),
    partial_update=extend_schema(summary="Partially update flight"),
    destroy=extend_schema(summary="Delete flight"),
)
@extend_schema(tags=["Flights"])
class FlightViewSet(viewsets.ModelViewSet):
    queryset = Flight.objects.all()
    serializer_class = FlightSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    filter_backends = (
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
    )
    filterset_class = FlightFilter
    search_fields = (
        "flight_number",
        "route__source__iata_code",
        "route__destination__iata_code"
    )
    ordering_fields = (
        "departure_time",
        "arrival_time",
    )

    def get_queryset(self):
        queryset = self.queryset

        if self.action in ("list", "retrieve"):
            queryset = queryset.annotate(
                available_seats=(
                        F("airplane__rows") * F("airplane__seats_in_row")
                        - Count("tickets")
                )
            )
            queryset = queryset.select_related(
                "route__source__city__country",
                "route__destination__city__country",
                "airplane__airplane_type"
            ).prefetch_related("crew", "tickets")

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return FlightListSerializer
        if self.action == "retrieve":
            return FlightDetailSerializer

        return FlightSerializer


@extend_schema_view(
    list=extend_schema(
        summary="List of orders",
        description="Retrieve a list of orders"
                    " created by the authenticated user.",
    ),
    retrieve=extend_schema(
        summary="Retrieve order",
        description="Retrieve detailed information about an"
                    " order belonging to the authenticated user.",
    ),
    create=extend_schema(
        summary="Create order",
        description="Create a new order for the authenticated user.",
    ),
    update=extend_schema(summary="Update order"),
    partial_update=extend_schema(summary="Partially update order"),
    destroy=extend_schema(summary="Delete order"),
)
@extend_schema(tags=["Orders"])
class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = (IsAuthenticated,)

    filter_backends = (OrderingFilter,)
    ordering_fields = ("created_at",)

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)

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
