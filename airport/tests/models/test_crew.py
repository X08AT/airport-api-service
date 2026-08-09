from django.test import TestCase

from airport.models import Crew


class CrewTests(TestCase):
    def setUp(self):
        self.crew = Crew.objects.create(
            first_name="Alex",
            last_name="Smith",
            position=Crew.Position.CAPTAIN,
        )

    def test_str_returns_full_name_and_position(self):
        self.assertEqual(str(self.crew), "Alex Smith (Captain)")

    def test_full_name_property(self):
        self.assertEqual(self.crew.full_name, "Alex Smith")
