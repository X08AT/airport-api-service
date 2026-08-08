from django.test import TestCase

from airport.models import Country, City


class CityTests(TestCase):
    def setUp(self):
        self.country = Country.objects.create(
            name="Ukraine"
        )
        self.city = City.objects.create(
            name="Kyiv",
            country=self.country
        )

    def test_str_returns_name_and_country(self):
        self.assertEqual(str(self.city), "Kyiv (Ukraine)")
