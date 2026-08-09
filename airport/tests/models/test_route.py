from django.core.exceptions import ValidationError
from django.test import TestCase

from airport.models import Country, City, Airport, Route


class RouteTests(TestCase):
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

    def test_str_returns_route_source_and_destination(self):
        self.assertEqual(
            str(self.route),
            "Boryspil (BOR) - Kyiv (Ukraine) ->"
            " Odesa International Airport (ODS) - Odesa (Ukraine)"
        )

    def test_cannot_create_route_with_same_airport(self):
        with self.assertRaises(ValidationError):
            Route.objects.create(
                source=self.source,
                destination=self.source,
                distance=100
            )

    def test_cannot_create_duplicate_route(self):
        with self.assertRaises(ValidationError):
            Route.objects.create(
                source=self.source,
                destination=self.destination,
                distance=500
            )
