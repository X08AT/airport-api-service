from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
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
    Ticket,
)


class TicketTests(TestCase):
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

        self.ticket = Ticket.objects.create(
            row=1,
            seat=2,
            flight=self.flight,
            order=self.order
        )

    def test_str_returns_row_seat(self):
        self.assertEqual(
            str(self.ticket),
            f"row:1, seat:2, flight:{self.flight.route}"
        )

    def test_cannot_create_ticket_with_invalid_row(self):
        with self.assertRaises(ValidationError):
            Ticket.objects.create(
                row=11,
                seat=2,
                flight=self.flight,
                order=self.order
            )

    def test_cannot_create_ticket_with_invalid_seat(self):
        with self.assertRaises(ValidationError):
            Ticket.objects.create(
                row=1,
                seat=7,
                flight=self.flight,
                order=self.order
            )

    def test_cannot_create_ticket_with_invalid_row_zero(self):
        with self.assertRaises(ValidationError):
            Ticket.objects.create(
                row=0,
                seat=2,
                flight=self.flight,
                order=self.order
            )

    def test_cannot_create_ticket_with_invalid_seat_zero(self):
        with self.assertRaises(ValidationError):
            Ticket.objects.create(
                row=1,
                seat=0,
                flight=self.flight,
                order=self.order
            )

    def test_cannot_create_ticket_for_taken_seat(self):
        with self.assertRaises(ValidationError):
            Ticket.objects.create(
                row=1,
                seat=2,
                flight=self.flight,
                order=self.order
            )

    def test_can_create_same_seat_on_different_flight(self):
        flight2 = Flight.objects.create(
            route=self.route,
            flight_number="KO227",
            airplane=self.airplane,
            departure_time=timezone.now(),
            arrival_time=timezone.now() + timedelta(hours=2)
        )

        ticket = Ticket.objects.create(
            row=1,
            seat=2,
            flight=flight2,
            order=self.order
        )

        self.assertEqual(ticket.row, 1)
        self.assertEqual(ticket.seat, 2)
