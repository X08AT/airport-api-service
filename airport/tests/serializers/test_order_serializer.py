from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

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
from airport.serializers import OrderSerializer


class OrderSerializerTest(TestCase):
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
        self.user = get_user_model().objects.create_user(
            email="test@test.com",
            password="test123"
        )

    def test_serializer_creates_order_with_tickets(self):
        serializer = OrderSerializer(
            data={
                "tickets": [
                    {
                        "row": 1,
                        "seat": 1,
                        "flight": self.flight.id,
                    },
                    {
                        "row": 1,
                        "seat": 2,
                        "flight": self.flight.id,
                    }
                ]
            }
        )
        self.assertTrue(serializer.is_valid())

        order = serializer.save(user=self.user)

        self.assertEqual(order.tickets.count(), 2)
        self.assertEqual(
            set(order.tickets.values_list("row", "seat")),
            {(1, 1), (1, 2)}
        )

    def test_serializer_rejects_empty_tickets(self):
        serializer = OrderSerializer(
            data={
                "tickets": []
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("tickets", serializer.errors)

    def test_serializer_rejects_invalid_ticket(self):
        serializer = OrderSerializer(
            data={
                "tickets": [
                    {
                        "row": 11,
                        "seat": 1,
                        "flight": self.flight.id,
                    }
                ]
            }
        )
        self.assertFalse(serializer.is_valid())
