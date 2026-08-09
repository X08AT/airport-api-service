from django.test import TestCase

from airport.models import AirplaneType


class AirplaneTypeTests(TestCase):
    def setUp(self):
        self.airplane_type = AirplaneType.objects.create(name="Boeing 777")

    def test_str_returns_name(self):
        self.assertEqual(str(self.airplane_type), "Boeing 777")
