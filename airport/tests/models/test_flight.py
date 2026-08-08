from datetime import timedelta

from django.core.exceptions import ValidationError
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


class FlightTests(TestCase):
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
        now = timezone.now()
        self.flight = Flight.objects.create(
            route=self.route,
            flight_number="KO226",
            airplane=self.airplane,
            departure_time=now,
            arrival_time=now + timedelta(hours=1),
            status=Flight.Status.SCHEDULED
        )
        self.flight.crew.add(self.crew1, self.crew2)

    def test_str_returns_flight_number(self):
        self.assertEqual(
            str(self.flight),
            f"KO226: {self.route}"
            f" ({self.flight.departure_time:%d/%m/%Y %H:%M})"
        )

    def test_arrival_time_before_departure_is_invalid(self):
        now = timezone.now()
        with self.assertRaises(ValidationError):
            Flight.objects.create(
                route=self.route,
                flight_number="KO451",
                airplane=self.airplane,
                departure_time=now,
                arrival_time=now - timedelta(hours=1),
                status=Flight.Status.SCHEDULED
            )

    def test_arrival_time_cannot_equal_departure_time(self):
        now = timezone.now()
        with self.assertRaises(ValidationError):
            Flight.objects.create(
                route=self.route,
                flight_number="KO451",
                airplane=self.airplane,
                departure_time=now,
                arrival_time=now,
                status=Flight.Status.SCHEDULED
            )

    def test_flight_can_be_created_when_arrival_is_after_departure(self):
        now = timezone.now()

        flight = Flight.objects.create(
            route=self.route,
            flight_number="KO451",
            airplane=self.airplane,
            departure_time=now,
            arrival_time=now + timedelta(hours=1),
            status=Flight.Status.SCHEDULED
        )

        self.assertGreater(flight.arrival_time, flight.departure_time)
