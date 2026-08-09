from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.reverse import reverse

from airport.models import Crew
from airport.serializers import CrewSerializer, CrewListSerializer

CREW_URL = reverse("airport:crew-list")


def detail_url(crew_id):
    return reverse(
        "airport:crew-detail",
        args=(crew_id,)
    )


def sample_crew(**params) -> Crew:
    defaults = {
        "first_name": "John",
        "last_name": "Doe",
        "position": Crew.Position.CAPTAIN
    }
    defaults.update(params)
    return Crew.objects.create(**defaults)


class UnauthenticatedCrewAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        response = self.client.get(CREW_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedCrewAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com",
            password="test123"
        )
        self.client.force_authenticate(self.user)

    def test_crew_list(self):
        sample_crew()
        sample_crew(first_name="Jane")
        response = self.client.get(CREW_URL)
        crews = Crew.objects.all()
        serializer = CrewListSerializer(crews, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], serializer.data)

    def test_crew_retrieve(self):
        crew = sample_crew()
        url = detail_url(crew.id)
        response = self.client.get(url)
        serializer = CrewSerializer(crew)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_create_crew_forbidden(self):
        payload = {
            "first_name": "John",
            "last_name": "Doe",
            "position": Crew.Position.CAPTAIN
        }
        response = self.client.post(CREW_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_crew_forbidden(self):
        crew = sample_crew()
        payload = {
            "first_name": "Jane"
        }
        response = self.client.patch(detail_url(crew.id), payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_crew_forbidden(self):
        crew = sample_crew()
        response = self.client.delete(detail_url(crew.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_search_crew_by_first_name(self):
        crew = sample_crew()
        crew2 = sample_crew(first_name="Jane")

        response = self.client.get(CREW_URL, {"search": "Jo"})

        serializer = CrewListSerializer(crew)
        serializer2 = CrewListSerializer(crew2)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(serializer.data, response.data["results"])
        self.assertNotIn(serializer2.data, response.data["results"])

    def test_search_crew_by_last_name(self):
        crew = sample_crew()
        crew2 = sample_crew(last_name="Smith")

        response = self.client.get(CREW_URL, {"search": "Do"})

        serializer = CrewListSerializer(crew)
        serializer2 = CrewListSerializer(crew2)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(serializer.data, response.data["results"])
        self.assertNotIn(serializer2.data, response.data["results"])

    def test_ordering_crew_by_first_name(self):
        sample_crew()
        sample_crew(first_name="Arthur")
        sample_crew(first_name="Mike")

        response = self.client.get(CREW_URL, {"ordering": "first_name"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        full_names = [crew["full_name"] for crew in response.data["results"]]

        self.assertEqual(full_names, ["Arthur Doe", "John Doe", "Mike Doe"])

    def test_ordering_crew_by_first_name_descending(self):
        sample_crew()
        sample_crew(first_name="Arthur")
        sample_crew(first_name="Mike")

        response = self.client.get(CREW_URL, {"ordering": "-first_name"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        full_names = [crew["full_name"] for crew in response.data["results"]]

        self.assertEqual(full_names, ["Mike Doe", "John Doe", "Arthur Doe"])

    def test_ordering_crew_by_last_name(self):
        sample_crew()
        sample_crew(last_name="Smith")
        sample_crew(last_name="Johnson")

        response = self.client.get(CREW_URL, {"ordering": "last_name"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        full_names = [crew["full_name"] for crew in response.data["results"]]

        self.assertEqual(
            full_names,
            ["John Doe", "John Johnson", "John Smith"]
        )

    def test_ordering_crew_by_last_name_descending(self):
        sample_crew()
        sample_crew(last_name="Smith")
        sample_crew(last_name="Johnson")

        response = self.client.get(CREW_URL, {"ordering": "-last_name"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        full_names = [crew["full_name"] for crew in response.data["results"]]

        self.assertEqual(
            full_names,
            ["John Smith", "John Johnson", "John Doe"]
        )

    def test_filter_crew_by_position(self):
        crew = sample_crew()
        crew2 = sample_crew(position=Crew.Position.FIRST_OFFICER)

        response = self.client.get(CREW_URL, {"position": crew.position})

        serializer = CrewListSerializer(crew)
        serializer2 = CrewListSerializer(crew2)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(serializer.data, response.data["results"])
        self.assertNotIn(serializer2.data, response.data["results"])


class AdminCrewAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com",
            password="test123",
            is_staff=True,
        )
        self.client.force_authenticate(self.user)

    def test_create_crew(self):
        payload = {
            "first_name": "John",
            "last_name": "Doe",
            "position": Crew.Position.CAPTAIN
        }
        response = self.client.post(CREW_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Crew.objects.filter(
            first_name="John",
            last_name="Doe",
            position=Crew.Position.CAPTAIN).exists()
                        )

    def test_update_crew(self):
        crew = sample_crew()
        payload = {
            "last_name": "Smith"
        }
        response = self.client.patch(detail_url(crew.id), payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        crew.refresh_from_db()
        self.assertEqual(crew.last_name, payload["last_name"])

    def test_delete_crew(self):
        crew = sample_crew()
        response = self.client.delete(detail_url(crew.id))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Crew.objects.filter(id=crew.id).exists())
