from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.reverse import reverse

from airport.models import AirplaneType
from airport.serializers import AirplaneTypeSerializer


AIRPLANE_TYPE_URL = reverse("airport:airplanetype-list")


def detail_url(airplane_type_id):
    return reverse(
        "airport:airplanetype-detail",
        args=(airplane_type_id,)
    )


def sample_airplane_type(**params) -> AirplaneType:
    defaults = {
        "name": "Boeing 777"
    }
    defaults.update(params)
    return AirplaneType.objects.create(**defaults)


class UnauthenticatedAirplaneTypeAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        response = self.client.get(AIRPLANE_TYPE_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedAirplaneTypeAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com",
            password="test123"
        )
        self.client.force_authenticate(self.user)

    def test_airplane_types_list(self):
        sample_airplane_type()
        sample_airplane_type(name="Boeing 435")
        response = self.client.get(AIRPLANE_TYPE_URL)
        airplane_types = AirplaneType.objects.all()
        serializer = AirplaneTypeSerializer(airplane_types, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], serializer.data)

    def test_airplane_type_retrieve(self):
        airplane_type = sample_airplane_type()
        url = detail_url(airplane_type.id)
        response = self.client.get(url)
        serializer = AirplaneTypeSerializer(airplane_type)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_create_airplane_type_forbidden(self):
        payload = {
            "name": "Boeing 777"
        }
        response = self.client.post(AIRPLANE_TYPE_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_airplane_type_forbidden(self):
        airplane_type = sample_airplane_type()
        payload = {
            "name": "Boeing 435"
        }
        response = self.client.patch(detail_url(airplane_type.id), payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_airplane_type_forbidden(self):
        airplane_type = sample_airplane_type()
        response = self.client.delete(detail_url(airplane_type.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_search_airplane_type_by_name(self):
        airplane_type = sample_airplane_type()
        airplane_type2 = sample_airplane_type(name="Airbus 25A")

        response = self.client.get(AIRPLANE_TYPE_URL, {"search": "Boeing"})

        serializer = AirplaneTypeSerializer(airplane_type)
        serializer2 = AirplaneTypeSerializer(airplane_type2)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(serializer.data, response.data["results"])
        self.assertNotIn(serializer2.data, response.data["results"])

    def test_ordering_airplane_type_by_name(self):
        sample_airplane_type(name="Boeing 435")
        sample_airplane_type(name="Airbus 25A")
        sample_airplane_type(name="Embraer 190")

        response = self.client.get(AIRPLANE_TYPE_URL, {"ordering": "name"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        names = [
            airplane_type["name"]
            for airplane_type in response.data["results"]
        ]

        self.assertEqual(names, ["Airbus 25A", "Boeing 435", "Embraer 190"])

    def test_ordering_airplane_type_by_name_descending(self):
        sample_airplane_type(name="Boeing 435")
        sample_airplane_type(name="Airbus 25A")
        sample_airplane_type(name="Embraer 190")

        response = self.client.get(AIRPLANE_TYPE_URL, {"ordering": "-name"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        names = [
            airplane_type["name"]
            for airplane_type in response.data["results"]
        ]

        self.assertEqual(names, ["Embraer 190", "Boeing 435", "Airbus 25A",])


class AdminAirplaneTypeAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com",
            password="test123",
            is_staff=True,
        )
        self.client.force_authenticate(self.user)

    def test_create_airplane_type(self):
        payload = {
            "name": "Boeing 435"
        }
        response = self.client.post(AIRPLANE_TYPE_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            AirplaneType.objects.filter(name="Boeing 435").exists()
        )

    def test_update_airplane_type(self):
        airplane_type = sample_airplane_type()
        payload = {
            "name": "Boeing 435"
        }
        response = self.client.patch(detail_url(airplane_type.id), payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        airplane_type.refresh_from_db()
        self.assertEqual(airplane_type.name, payload["name"])

    def test_delete_airplane_type(self):
        airplane_type = sample_airplane_type()
        response = self.client.delete(detail_url(airplane_type.id))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            AirplaneType.objects.filter(id=airplane_type.id).exists()
        )
