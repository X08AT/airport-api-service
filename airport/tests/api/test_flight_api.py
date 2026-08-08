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
    Crew,
    Flight,
)
from airport.serializers import (
    FlightListSerializer,
    FlightDetailSerializer,
)


FLIGHT_URL = reverse("airport:flight-list")


def detail_url(flight_id):
    return reverse(
        "airport:flight-detail",
        args=(flight_id,)
    )


def sample_country(**params) -> Country:
    defaults = {
        "name": "Ukraine",
    }
    defaults.update(params)

    return Country.objects.get_or_create(
        name=defaults["name"],
        defaults=defaults,
    )[0]


def sample_city(country=None, **params) -> City:
    if country is None:
        country = sample_country()

    defaults = {
        "name": "Kyiv",
        "country": country,
    }
    defaults.update(params)

    return City.objects.get_or_create(
        country=defaults["country"],
        name=defaults["name"],
        defaults={
            key: value
            for key, value in defaults.items()
            if key not in ("country", "name")
        },
    )[0]


def sample_airport(city=None, **params) -> Airport:
    if city is None:
        city = sample_city()

    defaults = {
        "name": "Boryspil International Airport",
        "city": city,
        "iata_code": "KBP",
    }
    defaults.update(params)

    return Airport.objects.get_or_create(
        iata_code=defaults["iata_code"],
        defaults=defaults,
    )[0]


def sample_route(source=None, destination=None, **params) -> Route:
    if source is None:
        source = sample_airport()

    if destination is None:
        country = source.city.country

        destination = sample_airport(
            city=sample_city(
                country=country,
                name="Lviv",
            ),
            name="Lviv International Airport",
            iata_code="LWO",
        )

    defaults = {
        "source": source,
        "destination": destination,
        "distance": 500,
    }
    defaults.update(params)

    return Route.objects.get_or_create(
        source=defaults["source"],
        destination=defaults["destination"],
        defaults={
            key: value
            for key, value in defaults.items()
            if key not in ("source", "destination")
        },
    )[0]


def sample_airplane_type(**params) -> AirplaneType:
    defaults = {
        "name": "Boeing 777",
    }
    defaults.update(params)

    return AirplaneType.objects.get_or_create(
        name=defaults["name"],
        defaults=defaults,
    )[0]


def sample_airplane(
    airplane_type=None,
    **params
) -> Airplane:
    if airplane_type is None:
        airplane_type = sample_airplane_type()

    defaults = {
        "registration_number": "UR-PSA",
        "airplane_type": airplane_type,
        "rows": 10,
        "seats_in_row": 6,
    }
    defaults.update(params)

    return Airplane.objects.get_or_create(
        registration_number=defaults["registration_number"],
        defaults=defaults,
    )[0]


def sample_crew(**params) -> Crew:
    defaults = {
        "first_name": "John",
        "last_name": "Smith",
        "position": Crew.Position.CAPTAIN,
    }
    defaults.update(params)

    return Crew.objects.create(**defaults)


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
        "route": route,
        "flight_number": "PS101",
        "airplane": airplane,
        "departure_time": (
            timezone.now() + timedelta(days=1)
        ),
        "arrival_time": (
            timezone.now() + timedelta(days=1, hours=3)
        ),
        "status": Flight.Status.SCHEDULED,
    }
    defaults.update(params)

    return Flight.objects.create(**defaults)


class UnauthenticatedFlightAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        response = self.client.get(FLIGHT_URL)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )


class AuthenticatedFlightAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user = get_user_model().objects.create_user(
            email="test@test.com",
            password="test123",
        )

        self.client.force_authenticate(self.user)

    def test_flight_list(self):
        flight1 = sample_flight()
        flight2 = sample_flight(
            flight_number="PS102",
        )

        response = self.client.get(FLIGHT_URL)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        result_ids = [
            flight["id"]
            for flight in response.data["results"]
        ]

        self.assertIn(
            flight1.id,
            result_ids,
        )

        self.assertIn(
            flight2.id,
            result_ids,
        )

    def test_flight_retrieve(self):
        flight = sample_flight()

        response = self.client.get(
            detail_url(flight.id)
        )

        serializer = FlightDetailSerializer(flight)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["id"],
            serializer.data["id"],
        )

        self.assertEqual(
            response.data["flight_number"],
            serializer.data["flight_number"],
        )

    def test_create_flight_forbidden(self):
        route = sample_route()
        airplane = sample_airplane()

        payload = {
            "route": route.id,
            "flight_number": "PS999",
            "airplane": airplane.id,
            "departure_time": (
                timezone.now() + timedelta(days=1)
            ).isoformat(),
            "arrival_time": (
                timezone.now() + timedelta(days=1, hours=3)
            ).isoformat(),
            "status": Flight.Status.SCHEDULED,
            "crew": [],
        }

        response = self.client.post(
            FLIGHT_URL,
            payload,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_update_flight_forbidden(self):
        flight = sample_flight()

        payload = {
            "flight_number": "PS555",
        }

        response = self.client.patch(
            detail_url(flight.id),
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_delete_flight_forbidden(self):
        flight = sample_flight()

        response = self.client.delete(
            detail_url(flight.id)
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_search_flight_by_flight_number(self):
        flight = sample_flight(
            flight_number="PS101",
        )

        flight2 = sample_flight(
            flight_number="LH202",
        )

        response = self.client.get(
            FLIGHT_URL,
            {"search": "PS101"},
        )

        serializer = FlightListSerializer(flight)
        serializer2 = FlightListSerializer(flight2)

        result_ids = [
            item["id"]
            for item in response.data["results"]
        ]

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            serializer.data["id"],
            result_ids,
        )

        self.assertNotIn(
            serializer2.data["id"],
            result_ids,
        )

    def test_search_flight_by_source_iata(self):
        flight = sample_flight()

        response = self.client.get(
            FLIGHT_URL,
            {"search": "KBP"},
        )

        result_ids = [
            item["id"]
            for item in response.data["results"]
        ]

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            flight.id,
            result_ids,
        )

    def test_search_flight_by_destination_iata(self):
        flight = sample_flight()

        response = self.client.get(
            FLIGHT_URL,
            {"search": "LWO"},
        )

        result_ids = [
            item["id"]
            for item in response.data["results"]
        ]

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            flight.id,
            result_ids,
        )

    def test_ordering_flight_by_departure_time(self):
        now = timezone.now()

        flight1 = sample_flight(
            flight_number="PS101",
            departure_time=now + timedelta(days=2),
            arrival_time=now + timedelta(days=2, hours=3),
        )

        flight2 = sample_flight(
            flight_number="PS102",
            departure_time=now + timedelta(days=1),
            arrival_time=now + timedelta(days=1, hours=3),
        )

        response = self.client.get(
            FLIGHT_URL,
            {"ordering": "departure_time"},
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        flight_ids = [
            flight["id"]
            for flight in response.data["results"]
        ]

        self.assertEqual(
            flight_ids,
            [flight2.id, flight1.id],
        )

    def test_ordering_flight_by_departure_time_descending(self):
        now = timezone.now()

        flight1 = sample_flight(
            flight_number="PS101",
            departure_time=now + timedelta(days=1),
            arrival_time=now + timedelta(days=1, hours=3),
        )

        flight2 = sample_flight(
            flight_number="PS102",
            departure_time=now + timedelta(days=2),
            arrival_time=now + timedelta(days=2, hours=3),
        )

        response = self.client.get(
            FLIGHT_URL,
            {"ordering": "-departure_time"},
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        flight_ids = [
            flight["id"]
            for flight in response.data["results"]
        ]

        self.assertEqual(
            flight_ids,
            [flight2.id, flight1.id],
        )

    def test_ordering_flight_by_arrival_time(self):
        now = timezone.now()

        flight1 = sample_flight(
            flight_number="PS101",
            departure_time=now + timedelta(days=1),
            arrival_time=now + timedelta(days=1, hours=5),
        )

        flight2 = sample_flight(
            flight_number="PS102",
            departure_time=now + timedelta(days=1),
            arrival_time=now + timedelta(days=1, hours=3),
        )

        response = self.client.get(
            FLIGHT_URL,
            {"ordering": "arrival_time"},
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        flight_ids = [
            flight["id"]
            for flight in response.data["results"]
        ]

        self.assertEqual(
            flight_ids,
            [flight2.id, flight1.id],
        )

    def test_filter_flight_by_status(self):
        flight = sample_flight(
            flight_number="PS101",
            status=Flight.Status.SCHEDULED,
        )

        flight2 = sample_flight(
            flight_number="PS102",
            status=Flight.Status.DELAYED,
        )

        response = self.client.get(
            FLIGHT_URL,
            {"status": Flight.Status.SCHEDULED},
        )

        result_ids = [
            item["id"]
            for item in response.data["results"]
        ]

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            flight.id,
            result_ids,
        )

        self.assertNotIn(
            flight2.id,
            result_ids,
        )

    def test_filter_flight_by_route(self):
        route1 = sample_route()

        country = sample_country(
            name="Poland",
        )

        city = sample_city(
            country=country,
            name="Warsaw",
        )

        airport = sample_airport(
            city=city,
            name="Warsaw Airport",
            iata_code="WAW",
        )

        route2 = sample_route(
            source=airport,
            destination=sample_airport(
                city=sample_city(
                    country=country,
                    name="Krakow",
                ),
                name="Krakow Airport",
                iata_code="KRK",
            ),
        )

        flight = sample_flight(
            route=route1,
            flight_number="PS101",
        )

        flight2 = sample_flight(
            route=route2,
            flight_number="PS102",
        )

        response = self.client.get(
            FLIGHT_URL,
            {"route": route1.id},
        )

        result_ids = [
            item["id"]
            for item in response.data["results"]
        ]

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            flight.id,
            result_ids,
        )

        self.assertNotIn(
            flight2.id,
            result_ids,
        )

    def test_filter_flight_by_airplane(self):
        airplane_type = sample_airplane_type(
            name="Boeing 777",
        )

        airplane_type2 = sample_airplane_type(
            name="Airbus A320",
        )

        airplane = sample_airplane(
            airplane_type=airplane_type,
            registration_number="UR-PSA",
        )

        airplane2 = sample_airplane(
            airplane_type=airplane_type2,
            registration_number="UR-PSB",
        )

        flight = sample_flight(
            airplane=airplane,
            flight_number="PS101",
        )

        flight2 = sample_flight(
            airplane=airplane2,
            flight_number="PS102",
        )

        response = self.client.get(
            FLIGHT_URL,
            {"airplane": airplane.id},
        )

        result_ids = [
            item["id"]
            for item in response.data["results"]
        ]

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            flight.id,
            result_ids,
        )

        self.assertNotIn(
            flight2.id,
            result_ids,
        )

    def test_filter_flight_by_departure_after(self):
        now = timezone.now()

        flight = sample_flight(
            flight_number="PS101",
            departure_time=now + timedelta(days=1),
            arrival_time=now + timedelta(days=1, hours=3),
        )

        flight2 = sample_flight(
            flight_number="PS102",
            departure_time=now + timedelta(days=5),
            arrival_time=now + timedelta(days=5, hours=3),
        )

        response = self.client.get(
            FLIGHT_URL,
            {
                "departure_after": (
                    now + timedelta(days=3)
                ).date(),
            },
        )

        result_ids = [
            item["id"]
            for item in response.data["results"]
        ]

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            flight2.id,
            result_ids,
        )

        self.assertNotIn(
            flight.id,
            result_ids,
        )

    def test_filter_flight_by_arrival_before(self):
        now = timezone.now()

        flight = sample_flight(
            flight_number="PS101",
            departure_time=now + timedelta(days=1),
            arrival_time=now + timedelta(days=1, hours=3),
        )

        flight2 = sample_flight(
            flight_number="PS102",
            departure_time=now + timedelta(days=5),
            arrival_time=now + timedelta(days=5, hours=3),
        )

        response = self.client.get(
            FLIGHT_URL,
            {
                "arrival_before": (
                    now + timedelta(days=3)
                ).date(),
            },
        )

        result_ids = [
            item["id"]
            for item in response.data["results"]
        ]

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            flight.id,
            result_ids,
        )

        self.assertNotIn(
            flight2.id,
            result_ids,
        )


class AdminFlightAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user = get_user_model().objects.create_user(
            email="admin@test.com",
            password="test123",
            is_staff=True,
        )

        self.client.force_authenticate(self.user)

    def test_create_flight(self):
        route = sample_route()
        airplane = sample_airplane()
        crew = sample_crew()

        departure_time = timezone.now() + timedelta(days=1)
        arrival_time = departure_time + timedelta(hours=3)

        payload = {
            "route": route.id,
            "flight_number": "PS999",
            "airplane": airplane.id,
            "crew": [crew.id],
            "departure_time": departure_time.isoformat(),
            "arrival_time": arrival_time.isoformat(),
            "status": Flight.Status.SCHEDULED,
        }

        response = self.client.post(
            FLIGHT_URL,
            payload
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertTrue(
            Flight.objects.filter(
                flight_number="PS999"
            ).exists()
        )

    def test_update_flight(self):
        flight = sample_flight()

        payload = {
            "flight_number": "PS555",
        }

        response = self.client.patch(
            detail_url(flight.id),
            payload
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        flight.refresh_from_db()

        self.assertEqual(
            flight.flight_number,
            payload["flight_number"],
        )

    def test_delete_flight(self):
        flight = sample_flight()

        response = self.client.delete(
            detail_url(flight.id)
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.assertFalse(
            Flight.objects.filter(
                id=flight.id
            ).exists()
        )
