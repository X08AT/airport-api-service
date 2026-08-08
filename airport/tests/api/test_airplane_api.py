from django.contrib.auth import get_user_model
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.reverse import reverse

from airport.models import AirplaneType, Airplane
from airport.serializers import (
    AirplaneListSerializer,
    AirplaneDetailSerializer
)

AIRPLANE_URL = reverse("airport:airplane-list")


def detail_url(airplane_id):
    return reverse("airport:airplane-detail", args=(airplane_id,))


def sample_airplane_type(**params) -> AirplaneType:
    defaults = {"name": "Boeing 777"}
    defaults.update(params)
    return AirplaneType.objects.create(**defaults)


def sample_airplane(airplane_type=None, **params) -> Airplane:
    if airplane_type is None:
        airplane_type = sample_airplane_type()
    defaults = {
        "registration_number": "UR-PSA",
        "airplane_type": airplane_type,
        "rows": 10,
        "seats_in_row": 6,
    }
    defaults.update(params)
    return Airplane.objects.create(**defaults)


class UnauthenticatedAirplaneAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        response = self.client.get(AIRPLANE_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedAirplaneAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com", password="test123"
        )
        self.client.force_authenticate(self.user)

    def test_airplane_list(self):
        airplane_type = sample_airplane_type()
        sample_airplane(airplane_type=airplane_type)
        sample_airplane(
            registration_number="OD-PSA",
            airplane_type=airplane_type
        )
        response = self.client.get(AIRPLANE_URL)
        airplanes = Airplane.objects.all()
        serializer = AirplaneListSerializer(airplanes, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], serializer.data)

    def test_airplane_retrieve(self):
        airplane = sample_airplane()
        url = detail_url(airplane.id)
        response = self.client.get(url)
        serializer = AirplaneDetailSerializer(airplane)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_create_airplane_forbidden(self):
        airplane_type = sample_airplane_type()
        payload = {
            "registration_number": "UR-PSA",
            "airplane_type": airplane_type.id,
            "rows": 10,
            "seats_in_row": 6,
        }
        response = self.client.post(AIRPLANE_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_airplane_forbidden(self):
        airplane = sample_airplane()
        payload = {
            "rows": 13,
        }
        response = self.client.patch(detail_url(airplane.id), payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_airplane_forbidden(self):
        airplane = sample_airplane()
        response = self.client.delete(detail_url(airplane.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_airplane_image_upload_forbidden(self):
        airplane = sample_airplane()

        image = Image.new("RGB", (100, 100))
        image_file = BytesIO()
        image.save(image_file, format="JPEG")
        image_file.seek(0)

        image = SimpleUploadedFile(
            "airplane.jpg",
            image_file.read(),
            content_type="image/jpeg",
        )

        response = self.client.post(
            detail_url(airplane.id) + "upload-image/",
            {"airplane_image": image},
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_search_airplane_by_registration_number(self):
        airplane_type = sample_airplane_type()
        airplane = sample_airplane(airplane_type=airplane_type)
        airplane2 = sample_airplane(
            registration_number="OD-PSA", airplane_type=airplane_type
        )

        response = self.client.get(AIRPLANE_URL, {"search": "UR"})

        serializer = AirplaneListSerializer(airplane)
        serializer2 = AirplaneListSerializer(airplane2)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(serializer.data, response.data["results"])
        self.assertNotIn(serializer2.data, response.data["results"])

    def test_ordering_airplane_by_registration_number(self):
        airplane_type = sample_airplane_type()

        sample_airplane(airplane_type=airplane_type)
        sample_airplane(
            registration_number="OD-PSA",
            airplane_type=airplane_type
        )
        sample_airplane(
            registration_number="OD-ASP",
            airplane_type=airplane_type
        )

        response = self.client.get(
            AIRPLANE_URL,
            {"ordering": "registration_number"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        registration_numbers = [
            airplane["registration_number"]
            for airplane in response.data["results"]
        ]

        self.assertEqual(registration_numbers, ["OD-ASP", "OD-PSA", "UR-PSA"])

    def test_ordering_airplane_by_registration_number_descending(self):
        airplane_type = sample_airplane_type()

        sample_airplane(airplane_type=airplane_type)
        sample_airplane(
            registration_number="OD-PSA",
            airplane_type=airplane_type
        )
        sample_airplane(
            registration_number="OD-ASP",
            airplane_type=airplane_type
        )

        response = self.client.get(
            AIRPLANE_URL,
            {"ordering": "-registration_number"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        registration_numbers = [
            airplane["registration_number"]
            for airplane in response.data["results"]
        ]

        self.assertEqual(registration_numbers, ["UR-PSA", "OD-PSA", "OD-ASP"])

    def test_filter_airplane_by_airplane_type(self):
        airplane_type = sample_airplane_type()
        airplane_type2 = sample_airplane_type(name="Airbus 24A")
        airplane = sample_airplane(airplane_type=airplane_type)
        airplane2 = sample_airplane(
            registration_number="OD-PSA", airplane_type=airplane_type2
        )

        response = self.client.get(
            AIRPLANE_URL,
            {"airplane_type": airplane_type.id}
        )

        serializer = AirplaneListSerializer(airplane)
        serializer2 = AirplaneListSerializer(airplane2)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(serializer.data, response.data["results"])
        self.assertNotIn(serializer2.data, response.data["results"])


class AdminAirplaneAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com",
            password="test123",
            is_staff=True,
        )
        self.client.force_authenticate(self.user)

    def test_create_airplane(self):
        airplane_type = sample_airplane_type()
        payload = {
            "registration_number": "UR-PSA",
            "airplane_type": airplane_type.id,
            "rows": 10,
            "seats_in_row": 6,
        }
        response = self.client.post(AIRPLANE_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Airplane.objects.filter(registration_number="UR-PSA").exists()
        )

    def test_update_airplane(self):
        airplane = sample_airplane()
        payload = {"registration_number": "OD-PSA"}
        response = self.client.patch(detail_url(airplane.id), payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        airplane.refresh_from_db()
        self.assertEqual(
            airplane.registration_number,
            payload["registration_number"]
        )

    def test_delete_airplane(self):
        airplane = sample_airplane()
        response = self.client.delete(detail_url(airplane.id))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Airplane.objects.filter(id=airplane.id).exists())

    def test_airplane_image_upload(self):
        airplane = sample_airplane()

        image = Image.new("RGB", (100, 100))
        image_file = BytesIO()
        image.save(image_file, format="JPEG")
        image_file.seek(0)

        image = SimpleUploadedFile(
            "airplane.jpg",
            image_file.read(),
            content_type="image/jpeg",
        )

        response = self.client.post(
            detail_url(airplane.id) + "upload-image/",
            {"airplane_image": image},
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        airplane.refresh_from_db()

        self.assertTrue(airplane.airplane_image)
