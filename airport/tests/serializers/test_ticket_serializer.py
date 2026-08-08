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
    Flight,
    Order,
    Ticket
)
from airport.serializers import TicketSerializer


class TicketSerializerTests(TestCase):
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
            name="Odesa Airport",
            city=self.city2,
            iata_code="ODS"
        )

        self.route = Route.objects.create(
            source=self.source,
            destination=self.destination,
            distance=476
        )

        self.airplane_type = AirplaneType.objects.create(
            name="Boeing 777"
        )

        self.airplane = Airplane.objects.create(
            registration_number="UR-PSA",
            airplane_type=self.airplane_type,
            rows=10,
            seats_in_row=6
        )

        now = timezone.now()

        self.flight = Flight.objects.create(
            route=self.route,
            flight_number="KO226",
            airplane=self.airplane,
            departure_time=now,
            arrival_time=now + timedelta(hours=2)
        )

        self.user = get_user_model().objects.create_user(
            email="test@test.com",
            password="password123"
        )

        self.order = Order.objects.create(
            user=self.user
        )

    def test_serializer_accepts_valid_ticket(self):
        serializer = TicketSerializer(
            data={
                "row": 1,
                "seat": 1,
                "flight": self.flight.id,
                "order": self.order.id,
            }
        )
        self.assertTrue(serializer.is_valid())

    def test_serializer_rejects_row_out_of_range(self):
        serializer = TicketSerializer(
            data={
                "row": 11,
                "seat": 1,
                "flight": self.flight.id,
                "order": self.order.id,
            }
        )
        self.assertFalse(serializer.is_valid())

    def test_serializer_rejects_seat_out_of_range(self):
        serializer = TicketSerializer(
            data={
                "row": 1,
                "seat": 7,
                "flight": self.flight.id,
                "order": self.order.id,
            }
        )
        self.assertFalse(serializer.is_valid())

    def test_serializer_rejects_zero_row(self):
        serializer = TicketSerializer(
            data={
                "row": 0,
                "seat": 1,
                "flight": self.flight.id,
                "order": self.order.id,
            }
        )
        self.assertFalse(serializer.is_valid())

    def test_serializer_rejects_zero_seat(self):
        serializer = TicketSerializer(
            data={
                "row": 1,
                "seat": 0,
                "flight": self.flight.id,
                "order": self.order.id,
            }
        )
        self.assertFalse(serializer.is_valid())

    def test_serializer_rejects_occupied_seat(self):
        Ticket.objects.create(
            row=1,
            seat=1,
            flight=self.flight,
            order=self.order,
        )
        serializer = TicketSerializer(
            data={
                "row": 1,
                "seat": 1,
                "flight": self.flight.id,
                "order": self.order.id,
            }
        )
        self.assertFalse(serializer.is_valid())

    def test_serializer_allows_same_seat_on_different_flight(self):
        now = timezone.now()
        flight2 = Flight.objects.create(
            route=self.route,
            flight_number="KO345",
            airplane=self.airplane,
            departure_time=now,
            arrival_time=now + timedelta(hours=2)
        )
        Ticket.objects.create(
            row=1,
            seat=1,
            flight=self.flight,
            order=self.order,
        )
        serializer = TicketSerializer(
            data={
                "row": 1,
                "seat": 1,
                "flight": flight2.id,
                "order": self.order.id,
            }
        )
        self.assertTrue(serializer.is_valid())

    def test_serializer_allows_updating_same_ticket(self):
        ticket = Ticket.objects.create(
            row=1,
            seat=1,
            flight=self.flight,
            order=self.order,
        )
        serializer = TicketSerializer(
            instance=ticket,
            data={
                "row": 1,
                "seat": 1,
            },
            partial=True
        )
        self.assertTrue(serializer.is_valid())
