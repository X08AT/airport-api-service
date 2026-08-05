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

