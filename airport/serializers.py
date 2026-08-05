from django.db import transaction
from rest_framework import serializers

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


class AirplaneTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AirplaneType
        fields = ("id", "name",)


class AirplaneSerializer(serializers.ModelSerializer):
    capacity = serializers.ReadOnlyField()

    class Meta:
        model = Airplane
        fields = (
            "id",
            "registration_number",
            "airplane_type",
            "rows",
            "seats_in_row",
            "capacity"
        )


class AirplaneListSerializer(AirplaneSerializer):
    airplane_type = serializers.CharField(
        source="airplane_type.name",
        read_only=True
    )

    class Meta(AirplaneSerializer.Meta):
        fields = (
            "id",
            "registration_number",
            "airplane_type",
            "rows",
            "seats_in_row",
            "capacity"
        )


class AirplaneDetailSerializer(AirplaneSerializer):
    airplane_type = AirplaneTypeSerializer(read_only=True)

    class Meta(AirplaneSerializer.Meta):
        fields = (
            "id",
            "registration_number",
            "airplane_type",
            "rows",
            "seats_in_row",
            "capacity"
        )


class CrewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = ("id", "first_name", "last_name", "position")


class CrewListSerializer(CrewSerializer):
    full_name = serializers.ReadOnlyField()

    class Meta(CrewSerializer.Meta):
        fields = ("id", "full_name", "position")


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ("id", "name")


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ("id", "name", "country")


class CityListSerializer(CitySerializer):
    country = serializers.CharField(source="country.name", read_only=True)

    class Meta(CitySerializer.Meta):
        fields = ("id", "name", "country")


class CityDetailSerializer(CitySerializer):
    country = CountrySerializer(read_only=True)

    class Meta(CitySerializer.Meta):
        fields = ("id", "name", "country")


class AirportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airport
        fields = ("id", "name", "city", "iata_code")


class AirportListSerializer(AirportSerializer):
    city = serializers.StringRelatedField(read_only=True)

    class Meta(AirportSerializer.Meta):
        fields = ("id", "name", "city", "iata_code")


class AirportDetailSerializer(AirportSerializer):
    city = CityDetailSerializer(read_only=True)

    class Meta(AirportSerializer.Meta):
        fields = ("id", "name", "city", "iata_code")


class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ("id", "source", "destination", "distance")


class RouteListSerializer(RouteSerializer):
    source = serializers.StringRelatedField(read_only=True)
    destination = serializers.StringRelatedField(read_only=True)

    class Meta(RouteSerializer.Meta):
        fields = ("id", "source", "destination", "distance")


class RouteDetailSerializer(RouteSerializer):
    source = AirportDetailSerializer(read_only=True)
    destination = AirportDetailSerializer(read_only=True)

    class Meta(RouteSerializer.Meta):
        fields = ("id", "source", "destination", "distance")


class FlightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flight
        fields = (
            "id",
            "route",
            "flight_number",
            "airplane",
            "crew",
            "departure_time",
            "arrival_time",
            "status"
        )


class FlightListSerializer(FlightSerializer):
    route = serializers.StringRelatedField(read_only=True)
    airplane = serializers.StringRelatedField(read_only=True)
    crew = CrewListSerializer(many=True, read_only=True)
    available_seats = serializers.IntegerField(read_only=True)

    class Meta(FlightSerializer.Meta):
        fields = (
            "id",
            "route",
            "flight_number",
            "airplane",
            "crew",
            "departure_time",
            "arrival_time",
            "available_seats",
            "status"
        )


class TakenSeatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("row", "seat")


class FlightDetailSerializer(FlightSerializer):
    route = RouteDetailSerializer(read_only=True)
    airplane = AirplaneDetailSerializer(read_only=True)
    crew = CrewSerializer(many=True, read_only=True)
    available_seats = serializers.IntegerField(read_only=True)
    taken_seats = TakenSeatSerializer(
        source="tickets",
        many=True,
        read_only=True
    )

    class Meta(FlightSerializer.Meta):
        fields = (
            "id",
            "route",
            "flight_number",
            "airplane",
            "crew",
            "departure_time",
            "arrival_time",
            "status",
            "available_seats",
            "taken_seats"
        )


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "flight")


class TicketListSerializer(TicketSerializer):
    flight = serializers.StringRelatedField(read_only=True)

    class Meta(TicketSerializer.Meta):
        fields = ("id", "row", "seat", "flight")


class FlightTicketSerializer(FlightSerializer):
    route = serializers.StringRelatedField(read_only=True)
    airplane = serializers.StringRelatedField(read_only=True)

    class Meta(FlightSerializer.Meta):
        fields = (
            "id",
            "route",
            "flight_number",
            "airplane",
            "departure_time",
            "arrival_time",
            "status"
        )


class TicketDetailSerializer(TicketSerializer):
    flight = FlightTicketSerializer(read_only=True)

    class Meta(TicketSerializer.Meta):
        fields = ("id", "row", "seat", "flight")


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, allow_empty=False)

    class Meta:
        model = Order
        fields = ("id", "created_at", "tickets")

    def create(self, validated_data):
        with transaction.atomic():
            tickets = validated_data.pop("tickets")
            order = Order.objects.create(**validated_data)
            for ticket in tickets:
                Ticket.objects.create(order=order, **ticket)
            return order


class OrderListSerializer(OrderSerializer):
    tickets = TicketListSerializer(many=True, read_only=True)

    class Meta(OrderSerializer.Meta):
        model = Order
        fields = ("id", "created_at", "tickets")


class OrderDetailSerializer(OrderSerializer):
    tickets = TicketDetailSerializer(many=True, read_only=True)

    class Meta(OrderSerializer.Meta):
        fields = ("id", "created_at", "tickets")
