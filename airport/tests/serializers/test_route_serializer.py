from django.test import TestCase

from airport.models import Country, City, Airport
from airport.serializers import RouteSerializer


class RouteSerializerTests(TestCase):
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

    def test_serializer_is_valid_with_correct_data(self):
        serializer = RouteSerializer(
            data={
                "source": self.source.id,
                "destination": self.destination.id,
                "distance": 476
            }
        )
        self.assertTrue(serializer.is_valid())

    def test_serializer_rejects_same_source_and_destination(self):
        serializer = RouteSerializer(
            data={
                "source": self.source.id,
                "destination": self.source.id,
                "distance": 476
            }
        )
        self.assertFalse(serializer.is_valid())
