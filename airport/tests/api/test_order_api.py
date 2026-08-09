from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.reverse import reverse

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
from airport.serializers import (
    OrderListSerializer,
    OrderDetailSerializer,
)

ORDER_URL = reverse("airport:order-list")


def detail_url(order_id):
    return reverse(
        "airport:order-detail",
        args=(order_id,)
    )


def sample_country(**params) -> Country:
    defaults = {
        "name": "Ukraine",
    }
    defaults.update(params)
    return Country.objects.create(**defaults)


def sample_city(country=None, **params) -> City:
    if country is None:
        country = sample_country()

    defaults = {
        "name": "Kyiv",
        "country": country,
    }
    defaults.update(params)
    return City.objects.create(**defaults)


def sample_airport(city=None, **params) -> Airport:
    if city is None:
        city = sample_city()

    defaults = {
        "name": "Boryspil International Airport",
        "city": city,
        "iata_code": "KBP",
    }
    defaults.update(params)
    return Airport.objects.create(**defaults)


def sample_route(source=None, destination=None, **params) -> Route:
    if source is None:
        source = sample_airport()

    if destination is None:
        country = source.city.country
        city = sample_city(country, name="Lviv")
        destination = sample_airport(
            city,
            name="Lviv International Airport",
            iata_code="LWO",
        )

    defaults = {
        "source": source,
        "destination": destination,
        "distance": 500,
    }
    defaults.update(params)
    return Route.objects.create(**defaults)


def sample_airplane_type(**params) -> AirplaneType:
    defaults = {
        "name": "Boeing 777",
    }
    defaults.update(params)
    return AirplaneType.objects.create(**defaults)


def sample_airplane(airplane_type=None, **params) -> Airplane:
    if airplane_type is None:
        airplane_type = sample_airplane_type()

    defaults = {
        "registration_number": "UR-PSA",
        "airplane_type": airplane_type,
        "rows": 10,
        "seats_in_row": 6,
    }
    defaults.update(params)
    return Airplane.objects.create(**defaults)


def sample_flight(
    route=None,
    airplane=None,
    **params
) -> Flight:
    if route is None:
        route = sample_route()

    if airplane is None:
        airplane = sample_airplane()

    defaults = {
        "flight_number": "PS101",
        "route": route,
        "airplane": airplane,
        "departure_time": timezone.now() + timedelta(hours=2),
        "arrival_time": timezone.now() + timedelta(hours=5),
    }
    defaults.update(params)
    return Flight.objects.create(**defaults)


def sample_order(user, **params) -> Order:
    defaults = {
        "user": user,
    }
    defaults.update(params)
    return Order.objects.create(**defaults)


def sample_ticket(order, flight, **params) -> Ticket:
    defaults = {
        "row": 1,
        "seat": 1,
        "flight": flight,
        "order": order,
    }
    defaults.update(params)
    return Ticket.objects.create(**defaults)


class UnauthenticatedOrderAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        response = self.client.get(ORDER_URL)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )


class AuthenticatedOrderAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com",
            password="test123",
        )
        self.client.force_authenticate(self.user)

    def test_order_list(self):
        order = sample_order(self.user)
        flight = sample_flight()
        sample_ticket(
            order=order,
            flight=flight,
        )

        response = self.client.get(ORDER_URL)

        orders = Order.objects.filter(user=self.user)
        serializer = OrderListSerializer(orders, many=True)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(
            response.data["results"],
            serializer.data
        )

    def test_order_retrieve(self):
        order = sample_order(self.user)
        flight = sample_flight()

        sample_ticket(
            order=order,
            flight=flight,
        )

        response = self.client.get(
            detail_url(order.id)
        )

        serializer = OrderDetailSerializer(order)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(
            response.data,
            serializer.data
        )

    def test_create_order(self):
        flight = sample_flight()

        payload = {
            "tickets": [
                {
                    "row": 1,
                    "seat": 1,
                    "flight": flight.id,
                }
            ]
        }

        response = self.client.post(
            ORDER_URL,
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

        order = Order.objects.get(
            id=response.data["id"]
        )

        self.assertEqual(
            order.user,
            self.user
        )

        self.assertTrue(
            Ticket.objects.filter(
                order=order,
                flight=flight,
                row=1,
                seat=1,
            ).exists()
        )

    def test_update_order(self):
        order = sample_order(self.user)
        flight = sample_flight()

        sample_ticket(
            order=order,
            flight=flight,
        )

        payload = {
            "tickets": [
                {
                    "row": 2,
                    "seat": 2,
                    "flight": flight.id,
                }
            ]
        }

        response = self.client.patch(
            detail_url(order.id),
            payload
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

    def test_delete_order(self):
        order = sample_order(self.user)

        response = self.client.delete(
            detail_url(order.id)
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT
        )

        self.assertFalse(
            Order.objects.filter(
                id=order.id
            ).exists()
        )

    def test_user_can_see_only_own_orders(self):
        own_order = sample_order(self.user)

        other_user = get_user_model().objects.create_user(
            email="other@test.com",
            password="test123",
        )

        other_order = sample_order(other_user)

        response = self.client.get(ORDER_URL)

        orders = [
            order["id"]
            for order in response.data["results"]
        ]

        self.assertIn(
            own_order.id,
            orders
        )
        self.assertNotIn(
            other_order.id,
            orders
        )

    def test_user_cannot_retrieve_other_users_order(self):
        other_user = get_user_model().objects.create_user(
            email="other@test.com",
            password="test123",
        )

        order = sample_order(other_user)

        response = self.client.get(
            detail_url(order.id)
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND
        )

    def test_user_cannot_update_other_users_order(self):
        other_user = get_user_model().objects.create_user(
            email="other@test.com",
            password="test123",
        )

        order = sample_order(other_user)

        response = self.client.patch(
            detail_url(order.id),
            {}
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND
        )

    def test_user_cannot_delete_other_users_order(self):
        other_user = get_user_model().objects.create_user(
            email="other@test.com",
            password="test123",
        )

        order = sample_order(other_user)

        response = self.client.delete(
            detail_url(order.id)
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND
        )

    def test_ordering_by_created_at(self):
        order1 = sample_order(self.user)
        order2 = sample_order(self.user)

        response = self.client.get(
            ORDER_URL,
            {"ordering": "created_at"},
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        order_ids = [
            order["id"]
            for order in response.data["results"]
        ]

        self.assertEqual(
            order_ids,
            [order1.id, order2.id],
        )

    def test_ordering_by_created_at_descending(self):
        order1 = sample_order(self.user)
        order2 = sample_order(self.user)

        response = self.client.get(
            ORDER_URL,
            {"ordering": "-created_at"},
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        order_ids = [
            order["id"]
            for order in response.data["results"]
        ]

        self.assertEqual(
            order_ids,
            [order2.id, order1.id],
        )
