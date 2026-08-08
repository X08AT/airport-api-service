from django.test import TestCase

from airport.models import Country


class CountryTests(TestCase):
    def setUp(self):
        self.country = Country.objects.create(
            name="Ukraine"
        )

    def test_str_returns_name(self):
        self.assertEqual(str(self.country), "Ukraine")
