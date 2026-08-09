from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.reverse import reverse

from airport.models import Country, City, Airport, Route
from airport.serializers import RouteListSerializer, RouteDetailSerializer


ROUTE_URL = reverse("airport:route-list")


def detail_url(route_id):
    return reverse(
        "airport:route-detail",
        args=(route_id,)
    )


def sample_country(**params) -> Country:
    defaults = {
        "name": "Ukraine"
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
        destination = sample_airport(
            city=sample_city(
                country=source.city.country,
                name="Lviv"
            ),
            name="Lviv International Airport",
            iata_code="LWO"
        )

    defaults = {
        "source": source,
        "destination": destination,
        "distance": 500,
    }
    defaults.update(params)
    return Route.objects.create(**defaults)


class UnauthenticatedRouteAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        response = self.client.get(ROUTE_URL)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )


class AuthenticatedRouteAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com",
            password="test123"
        )
        self.client.force_authenticate(self.user)

    def test_route_list(self):
        country = sample_country()

        city1 = sample_city(
            country=country,
            name="Kyiv"
        )
        city2 = sample_city(
            country=country,
            name="Lviv"
        )

        airport1 = sample_airport(
            city=city1,
            name="Boryspil International Airport",
            iata_code="KBP"
        )
        airport2 = sample_airport(
            city=city2,
            name="Lviv International Airport",
            iata_code="LWO"
        )

        sample_route(
            source=airport1,
            destination=airport2
        )

        response = self.client.get(ROUTE_URL)

        routes = Route.objects.all()
        serializer = RouteListSerializer(
            routes,
            many=True
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(
            response.data["results"],
            serializer.data
        )

    def test_route_retrieve(self):
        route = sample_route()
        url = detail_url(route.id)

        response = self.client.get(url)
        serializer = RouteDetailSerializer(route)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(
            response.data,
            serializer.data
        )

    def test_create_route_forbidden(self):
        country = sample_country()

        city1 = sample_city(
            country=country,
            name="Kyiv"
        )
        city2 = sample_city(
            country=country,
            name="Lviv"
        )

        source = sample_airport(
            city=city1,
            name="Boryspil International Airport",
            iata_code="KBP"
        )
        destination = sample_airport(
            city=city2,
            name="Lviv International Airport",
            iata_code="LWO"
        )

        payload = {
            "source": source.id,
            "destination": destination.id,
            "distance": 500,
        }

        response = self.client.post(
            ROUTE_URL,
            payload
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN
        )

    def test_update_route_forbidden(self):
        route = sample_route()

        payload = {
            "distance": 600
        }

        response = self.client.patch(
            detail_url(route.id),
            payload
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN
        )

    def test_delete_route_forbidden(self):
        route = sample_route()

        response = self.client.delete(
            detail_url(route.id)
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN
        )

    def test_search_route_by_source_city_name(self):
        country = sample_country()

        kyiv = sample_city(
            country=country,
            name="Kyiv"
        )
        lviv = sample_city(
            country=country,
            name="Lviv"
        )
        odesa = sample_city(
            country=country,
            name="Odesa"
        )

        source = sample_airport(
            city=kyiv,
            name="Boryspil International Airport",
            iata_code="KBP"
        )
        destination = sample_airport(
            city=lviv,
            name="Lviv International Airport",
            iata_code="LWO"
        )

        source2 = sample_airport(
            city=odesa,
            name="Odesa International Airport",
            iata_code="ODS"
        )
        destination2 = sample_airport(
            city=lviv,
            name="Lviv Airport",
            iata_code="LVI"
        )

        route = sample_route(
            source=source,
            destination=destination
        )
        route2 = sample_route(
            source=source2,
            destination=destination2,
            distance=700
        )

        response = self.client.get(
            ROUTE_URL,
            {"search": "Kyiv"}
        )

        serializer = RouteListSerializer(route)
        serializer2 = RouteListSerializer(route2)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertIn(
            serializer.data,
            response.data["results"]
        )
        self.assertNotIn(
            serializer2.data,
            response.data["results"]
        )

    def test_search_route_by_destination_city_name(self):
        country = sample_country()

        kyiv = sample_city(
            country=country,
            name="Kyiv"
        )
        lviv = sample_city(
            country=country,
            name="Lviv"
        )
        odesa = sample_city(
            country=country,
            name="Odesa"
        )

        source = sample_airport(
            city=kyiv,
            name="Boryspil International Airport",
            iata_code="KBP"
        )
        destination = sample_airport(
            city=lviv,
            name="Lviv International Airport",
            iata_code="LWO"
        )

        source2 = sample_airport(
            city=kyiv,
            name="Kyiv Airport",
            iata_code="KIV"
        )
        destination2 = sample_airport(
            city=odesa,
            name="Odesa International Airport",
            iata_code="ODS"
        )

        route = sample_route(
            source=source,
            destination=destination
        )
        route2 = sample_route(
            source=source2,
            destination=destination2,
            distance=700
        )

        response = self.client.get(
            ROUTE_URL,
            {"search": "Lviv"}
        )

        serializer = RouteListSerializer(route)
        serializer2 = RouteListSerializer(route2)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertIn(
            serializer.data,
            response.data["results"]
        )
        self.assertNotIn(
            serializer2.data,
            response.data["results"]
        )

    def test_search_route_by_source_iata_code(self):
        country = sample_country()

        city1 = sample_city(
            country=country,
            name="Kyiv"
        )
        city2 = sample_city(
            country=country,
            name="Lviv"
        )
        city3 = sample_city(
            country=country,
            name="Odesa"
        )

        source = sample_airport(
            city=city1,
            name="Boryspil International Airport",
            iata_code="KBP"
        )
        destination = sample_airport(
            city=city2,
            name="Lviv International Airport",
            iata_code="LWO"
        )

        source2 = sample_airport(
            city=city3,
            name="Odesa International Airport",
            iata_code="ODS"
        )
        destination2 = sample_airport(
            city=city2,
            name="Lviv Airport",
            iata_code="LVI"
        )

        route = sample_route(
            source=source,
            destination=destination
        )
        route2 = sample_route(
            source=source2,
            destination=destination2,
            distance=700
        )

        response = self.client.get(
            ROUTE_URL,
            {"search": "KBP"}
        )

        serializer = RouteListSerializer(route)
        serializer2 = RouteListSerializer(route2)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertIn(
            serializer.data,
            response.data["results"]
        )
        self.assertNotIn(
            serializer2.data,
            response.data["results"]
        )

    def test_search_route_by_destination_iata_code(self):
        country = sample_country()

        city1 = sample_city(
            country=country,
            name="Kyiv"
        )
        city2 = sample_city(
            country=country,
            name="Lviv"
        )
        city3 = sample_city(
            country=country,
            name="Odesa"
        )

        source = sample_airport(
            city=city1,
            name="Boryspil International Airport",
            iata_code="KBP"
        )
        destination = sample_airport(
            city=city2,
            name="Lviv International Airport",
            iata_code="LWO"
        )

        source2 = sample_airport(
            city=city1,
            name="Kyiv Airport",
            iata_code="KIV"
        )
        destination2 = sample_airport(
            city=city3,
            name="Odesa International Airport",
            iata_code="ODS"
        )

        route = sample_route(
            source=source,
            destination=destination
        )
        route2 = sample_route(
            source=source2,
            destination=destination2,
            distance=700
        )

        response = self.client.get(
            ROUTE_URL,
            {"search": "LWO"}
        )

        serializer = RouteListSerializer(route)
        serializer2 = RouteListSerializer(route2)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertIn(
            serializer.data,
            response.data["results"]
        )
        self.assertNotIn(
            serializer2.data,
            response.data["results"]
        )

    def test_ordering_route_by_distance(self):
        country = sample_country()

        kyiv = sample_city(
            country=country,
            name="Kyiv"
        )
        odesa = sample_city(
            country=country,
            name="Odesa"
        )
        warsaw = sample_city(
            country=country,
            name="Warsaw"
        )
        berlin = sample_city(
            country=country,
            name="Berlin"
        )
        paris = sample_city(
            country=country,
            name="Paris"
        )

        kyiv_airport = sample_airport(
            city=kyiv,
            name="Boryspil International Airport",
            iata_code="KBP"
        )
        lviv_airport = sample_airport(
            city=sample_city(
                country=country,
                name="Lviv"
            ),
            name="Lviv International Airport",
            iata_code="LWO"
        )

        odesa_airport = sample_airport(
            city=odesa,
            name="Odesa International Airport",
            iata_code="ODS"
        )
        warsaw_airport = sample_airport(
            city=warsaw,
            name="Warsaw Airport",
            iata_code="WAW"
        )

        berlin_airport = sample_airport(
            city=berlin,
            name="Berlin Airport",
            iata_code="BER"
        )
        paris_airport = sample_airport(
            city=paris,
            name="Paris Airport",
            iata_code="PAR"
        )

        sample_route(
            source=kyiv_airport,
            destination=lviv_airport,
            distance=500
        )
        sample_route(
            source=odesa_airport,
            destination=warsaw_airport,
            distance=1000
        )
        sample_route(
            source=berlin_airport,
            destination=paris_airport,
            distance=1500
        )

        response = self.client.get(
            ROUTE_URL,
            {"ordering": "distance"}
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        distances = [
            route["distance"]
            for route in response.data["results"]
        ]

        self.assertEqual(
            distances,
            [500, 1000, 1500]
        )

    def test_ordering_route_by_distance_descending(self):
        country = sample_country()

        kyiv = sample_city(
            country=country,
            name="Kyiv"
        )
        lviv = sample_city(
            country=country,
            name="Lviv"
        )
        odesa = sample_city(
            country=country,
            name="Odesa"
        )
        warsaw = sample_city(
            country=country,
            name="Warsaw"
        )
        berlin = sample_city(
            country=country,
            name="Berlin"
        )
        paris = sample_city(
            country=country,
            name="Paris"
        )

        kyiv_airport = sample_airport(
            city=kyiv,
            name="Boryspil International Airport",
            iata_code="KBP"
        )
        lviv_airport = sample_airport(
            city=lviv,
            name="Lviv International Airport",
            iata_code="LWO"
        )

        odesa_airport = sample_airport(
            city=odesa,
            name="Odesa International Airport",
            iata_code="ODS"
        )
        warsaw_airport = sample_airport(
            city=warsaw,
            name="Warsaw Airport",
            iata_code="WAW"
        )

        berlin_airport = sample_airport(
            city=berlin,
            name="Berlin Airport",
            iata_code="BER"
        )
        paris_airport = sample_airport(
            city=paris,
            name="Paris Airport",
            iata_code="PAR"
        )

        sample_route(
            source=kyiv_airport,
            destination=lviv_airport,
            distance=500
        )
        sample_route(
            source=odesa_airport,
            destination=warsaw_airport,
            distance=1000
        )
        sample_route(
            source=berlin_airport,
            destination=paris_airport,
            distance=1500
        )

        response = self.client.get(
            ROUTE_URL,
            {"ordering": "-distance"}
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        distances = [
            route["distance"]
            for route in response.data["results"]
        ]

        self.assertEqual(
            distances,
            [1500, 1000, 500]
        )

    def test_filter_route_by_source(self):
        country = sample_country()

        city1 = sample_city(
            country=country,
            name="Kyiv"
        )
        city2 = sample_city(
            country=country,
            name="Lviv"
        )
        city3 = sample_city(
            country=country,
            name="Odesa"
        )

        source = sample_airport(
            city=city1,
            name="Boryspil International Airport",
            iata_code="KBP"
        )
        destination = sample_airport(
            city=city2,
            name="Lviv International Airport",
            iata_code="LWO"
        )
        source2 = sample_airport(
            city=city3,
            name="Odesa International Airport",
            iata_code="ODS"
        )

        route = sample_route(
            source=source,
            destination=destination
        )
        route2 = sample_route(
            source=source2,
            destination=destination,
            distance=700
        )

        response = self.client.get(
            ROUTE_URL,
            {"source": source.id}
        )

        serializer = RouteListSerializer(route)
        serializer2 = RouteListSerializer(route2)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertIn(
            serializer.data,
            response.data["results"]
        )
        self.assertNotIn(
            serializer2.data,
            response.data["results"]
        )

    def test_filter_route_by_destination(self):
        country = sample_country()

        city1 = sample_city(
            country=country,
            name="Kyiv"
        )
        city2 = sample_city(
            country=country,
            name="Lviv"
        )
        city3 = sample_city(
            country=country,
            name="Odesa"
        )

        source = sample_airport(
            city=city1,
            name="Boryspil International Airport",
            iata_code="KBP"
        )
        destination = sample_airport(
            city=city2,
            name="Lviv International Airport",
            iata_code="LWO"
        )
        destination2 = sample_airport(
            city=city3,
            name="Odesa International Airport",
            iata_code="ODS"
        )

        route = sample_route(
            source=source,
            destination=destination
        )
        route2 = sample_route(
            source=source,
            destination=destination2,
            distance=700
        )

        response = self.client.get(
            ROUTE_URL,
            {"destination": destination.id}
        )

        serializer = RouteListSerializer(route)
        serializer2 = RouteListSerializer(route2)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertIn(
            serializer.data,
            response.data["results"]
        )
        self.assertNotIn(
            serializer2.data,
            response.data["results"]
        )


class AdminRouteAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com",
            password="test123",
            is_staff=True,
        )
        self.client.force_authenticate(self.user)

    def test_create_route(self):
        country = sample_country()

        city1 = sample_city(
            country=country,
            name="Kyiv"
        )
        city2 = sample_city(
            country=country,
            name="Lviv"
        )

        source = sample_airport(
            city=city1,
            name="Boryspil International Airport",
            iata_code="KBP"
        )
        destination = sample_airport(
            city=city2,
            name="Lviv International Airport",
            iata_code="LWO"
        )

        payload = {
            "source": source.id,
            "destination": destination.id,
            "distance": 500,
        }

        response = self.client.post(
            ROUTE_URL,
            payload
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )
        self.assertTrue(
            Route.objects.filter(
                source=source,
                destination=destination,
                distance=500
            ).exists()
        )

    def test_update_route(self):
        route = sample_route()

        payload = {
            "distance": 600
        }

        response = self.client.patch(
            detail_url(route.id),
            payload
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        route.refresh_from_db()

        self.assertEqual(
            route.distance,
            payload["distance"]
        )

    def test_delete_route(self):
        route = sample_route()

        response = self.client.delete(
            detail_url(route.id)
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT
        )

        self.assertFalse(
            Route.objects.filter(
                id=route.id
            ).exists()
        )
