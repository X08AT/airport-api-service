from django.test import TestCase

from airport.models import Airplane, AirplaneType


class AirplaneTests(TestCase):
    def setUp(self):
        self.airplane_type = AirplaneType.objects.create(name="Boeing 777")
        self.airplane = Airplane.objects.create(
            registration_number="UR-PSA",
            airplane_type=self.airplane_type,
            rows=10,
            seats_in_row=6
        )

    def test_str_returns_airplane_type_and_registration_number(self):
        self.assertEqual(str(self.airplane), "Boeing 777 (UR-PSA)")

    def test_capacity_is_calculated_correctly(self):
        self.assertEqual(self.airplane.capacity, 60)
