from django.test import TestCase

from airport.models import Country, City, Airport


class AirportTests(TestCase):
    def setUp(self):
        self.country = Country.objects.create(
            name="Ukraine"
        )
        self.city = City.objects.create(
            name="Kyiv",
            country=self.country
        )
        self.airport = Airport.objects.create(
            name="Boryspil",
            city=self.city,
            iata_code="BOR"
        )

    def test_str_returns_name_iata_code_and_city(self):
        self.assertEqual(str(self.airport), "Boryspil (BOR) - Kyiv (Ukraine)")
