from django.db.models import Prefetch, Count, F
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from airport.filters import FlightFilter
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
    AirplaneImageSerializer, CountryImageSerializer, CountryListAndRetrieveSerializer, CityImageSerializer,
    AirportImageSerializer
)


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


class AirplaneViewSet(viewsets.ModelViewSet):
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

    @action(
        methods=["post"],
        detail=True,
        url_path="upload-image"
    )
    def upload_image(self, request, pk=None):
        airplane = self.get_object()
        serializer = self.get_serializer(airplane, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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


class CountryViewSet(viewsets.ModelViewSet):
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

    @action(
        methods=["post"],
        detail=True,
        url_path="upload-image"
    )
    def upload_image(self, request, pk=None):
        country = self.get_object()
        serializer = self.get_serializer(country, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CityViewSet(viewsets.ModelViewSet):
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

    @action(
        methods=["post"],
        detail=True,
        url_path="upload-image"
    )
    def upload_image(self, request, pk=None):
        city = self.get_object()
        serializer = self.get_serializer(city, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AirportViewSet(viewsets.ModelViewSet):
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

    @action(
        methods=["post"],
        detail=True,
        url_path="upload-image"
    )
    def upload_image(self, request, pk=None):
        city = self.get_object()
        serializer = self.get_serializer(city, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
