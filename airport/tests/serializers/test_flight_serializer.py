from datetime import timedelta

from django.utils import timezone
from django.test import TestCase

from airport.models import (
    Country,
    City,
    Airport,
    Route,
    AirplaneType,
    Airplane,
    Crew,
    Flight
)
from airport.serializers import FlightSerializer


class FlightSerializerTests(TestCase):
    def setUp(self):
        self.country = Country.objects.create(
            name="Ukraine"
        )
        self.city1 = City.objects.create(
            name="Kyiv",
            country=self.country
        )
        self.city2 = City.objects.create(
            name="Odesa",
            country=self.country
        )
        self.source = Airport.objects.create(
            name="Boryspil",
            city=self.city1,
            iata_code="BOR"
        )
        self.destination = Airport.objects.create(
            name="Odesa International Airport",
            city=self.city2,
            iata_code="ODS"
        )
        self.route = Route.objects.create(
            source=self.source,
            destination=self.destination,
            distance=476
        )
        self.airplane_type = AirplaneType.objects.create(name="Boeing 777")
        self.airplane = Airplane.objects.create(
            registration_number="UR-PSA",
            airplane_type=self.airplane_type,
            rows=10,
            seats_in_row=6
        )
        self.crew1 = Crew.objects.create(
            first_name="Alex",
            last_name="Smith",
            position=Crew.Position.CAPTAIN,
        )
        self.crew2 = Crew.objects.create(
            first_name="John",
            last_name="Doe",
            position=Crew.Position.FIRST_OFFICER,
        )

    def test_serializer_is_valid_with_correct_data(self):
        now = timezone.now()
        serializer = FlightSerializer(
            data={
                "route": self.route.id,
                "flight_number": "KO226",
                "airplane": self.airplane.id,
                "crew": [self.crew1.id, self.crew2.id],
                "departure_time": now,
                "arrival_time": now + timedelta(hours=1),
                "status": Flight.Status.SCHEDULED
            }
        )
        self.assertTrue(serializer.is_valid())

    def test_serializer_rejects_if_arrival_before_departure(self):
        now = timezone.now()
        serializer = FlightSerializer(
            data={
                "route": self.route.id,
                "flight_number": "KO226",
                "airplane": self.airplane.id,
                "crew": [self.crew1.id, self.crew2.id],
                "departure_time": now,
                "arrival_time": now - timedelta(hours=1),
                "status": Flight.Status.SCHEDULED
            }
        )
        self.assertFalse(serializer.is_valid())

    def test_serializer_rejects_if_arrival_equals_departure(self):
        now = timezone.now()
        serializer = FlightSerializer(
            data={
                "route": self.route.id,
                "flight_number": "KO226",
                "airplane": self.airplane.id,
                "crew": [self.crew1.id, self.crew2.id],
                "departure_time": now,
                "arrival_time": now,
                "status": Flight.Status.SCHEDULED
            }
        )
        self.assertFalse(serializer.is_valid())

    def test_serializer_rejects_patch_with_invalid_arrival_time(self):
        now = timezone.now()
        flight = Flight.objects.create(
            route=self.route,
            flight_number="KO226",
            airplane=self.airplane,
            departure_time=now,
            arrival_time=now + timedelta(hours=1),
            status=Flight.Status.SCHEDULED
        )
        flight.crew.add(self.crew1, self.crew2)
        serializer = FlightSerializer(
            instance=flight,
            data={
                "arrival_time": now - timedelta(hours=1),
            },
            partial=True
        )
        self.assertFalse(serializer.is_valid())
