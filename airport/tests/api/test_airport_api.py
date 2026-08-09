from django.contrib.auth import get_user_model
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.reverse import reverse

from airport.models import Country, City, Airport
from airport.serializers import AirportListSerializer, AirportDetailSerializer

AIRPORT_URL = reverse("airport:airport-list")


def detail_url(airport_id):
    return reverse("airport:airport-detail", args=(airport_id,))


def sample_country(**params) -> Country:
    defaults = {"name": "Ukraine"}
    defaults.update(params)
    return Country.objects.create(**defaults)


def sample_city(country=None, **params) -> City:
    if country is None:
        country = sample_country()

    defaults = {
        "name": "Kyiv",
        "country": country,
    }
    defaults.update(params)
    return City.objects.create(**defaults)


def sample_airport(city=None, **params) -> Airport:
    if city is None:
        city = sample_city()

    defaults = {
        "name": "Boryspil International Airport",
        "city": city,
        "iata_code": "KBP",
    }
    defaults.update(params)
    return Airport.objects.create(**defaults)


class UnauthenticatedAirportAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        response = self.client.get(AIRPORT_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedAirportAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com", password="test123"
        )
        self.client.force_authenticate(self.user)

    def test_airport_list(self):
        city = sample_city()

        sample_airport(city=city)
        sample_airport(
            name="Lviv International Airport",
            iata_code="LWO",
            city=city
        )

        response = self.client.get(AIRPORT_URL)

        airports = Airport.objects.all()
        serializer = AirportListSerializer(airports, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], serializer.data)

    def test_airport_retrieve(self):
        airport = sample_airport()
        url = detail_url(airport.id)

        response = self.client.get(url)
        serializer = AirportDetailSerializer(airport)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_create_airport_forbidden(self):
        city = sample_city()

        payload = {
            "name": "Boryspil International Airport",
            "city": city.id,
            "iata_code": "KBP",
        }

        response = self.client.post(AIRPORT_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_airport_forbidden(self):
        airport = sample_airport()

        payload = {
            "name": "New Airport Name",
        }

        response = self.client.patch(detail_url(airport.id), payload)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_airport_forbidden(self):
        airport = sample_airport()

        response = self.client.delete(detail_url(airport.id))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_airport_image_upload_forbidden(self):
        airport = sample_airport()

        image = Image.new("RGB", (100, 100))
        image_file = BytesIO()
        image.save(image_file, format="JPEG")
        image_file.seek(0)

        image = SimpleUploadedFile(
            "airport.jpg",
            image_file.read(),
            content_type="image/jpeg",
        )

        response = self.client.post(
            detail_url(airport.id) + "upload-image/",
            {"airport_image": image},
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_search_airport_by_name(self):
        city = sample_city()

        airport = sample_airport(city=city)
        airport2 = sample_airport(
            name="Lviv International Airport", iata_code="LWO", city=city
        )

        response = self.client.get(AIRPORT_URL, {"search": "Boryspil"})

        serializer = AirportListSerializer(airport)
        serializer2 = AirportListSerializer(airport2)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(serializer.data, response.data["results"])
        self.assertNotIn(serializer2.data, response.data["results"])

    def test_search_airport_by_iata_code(self):
        city = sample_city()

        airport = sample_airport(city=city)
        airport2 = sample_airport(
            name="Lviv International Airport", iata_code="LWO", city=city
        )

        response = self.client.get(AIRPORT_URL, {"search": "KBP"})

        serializer = AirportListSerializer(airport)
        serializer2 = AirportListSerializer(airport2)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(serializer.data, response.data["results"])
        self.assertNotIn(serializer2.data, response.data["results"])

    def test_search_airport_by_city_name(self):
        country = sample_country()

        city = sample_city(country=country, name="Kyiv")
        city2 = sample_city(country=country, name="Lviv")

        airport = sample_airport(city=city)
        airport2 = sample_airport(
            name="Lviv International Airport", iata_code="LWO", city=city2
        )

        response = self.client.get(AIRPORT_URL, {"search": "Kyiv"})

        serializer = AirportListSerializer(airport)
        serializer2 = AirportListSerializer(airport2)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(serializer.data, response.data["results"])
        self.assertNotIn(serializer2.data, response.data["results"])

    def test_ordering_airport_by_name(self):
        city = sample_city()

        sample_airport(
            city=city, name="Boryspil International Airport", iata_code="KBP"
        )
        sample_airport(
            city=city,
            name="Lviv International Airport",
            iata_code="LWO"
        )
        sample_airport(
            city=city,
            name="Odesa International Airport",
            iata_code="ODS"
        )

        response = self.client.get(AIRPORT_URL, {"ordering": "name"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        names = [airport["name"] for airport in response.data["results"]]

        self.assertEqual(
            names,
            [
                "Boryspil International Airport",
                "Lviv International Airport",
                "Odesa International Airport",
            ],
        )

    def test_ordering_airport_by_name_descending(self):
        city = sample_city()

        sample_airport(
            city=city, name="Boryspil International Airport", iata_code="KBP"
        )
        sample_airport(
            city=city,
            name="Lviv International Airport",
            iata_code="LWO"
        )
        sample_airport(
            city=city,
            name="Odesa International Airport",
            iata_code="ODS"
        )

        response = self.client.get(AIRPORT_URL, {"ordering": "-name"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        names = [airport["name"] for airport in response.data["results"]]

        self.assertEqual(
            names,
            [
                "Odesa International Airport",
                "Lviv International Airport",
                "Boryspil International Airport",
            ],
        )

    def test_filter_airport_by_city(self):
        country = sample_country()

        city = sample_city(country=country, name="Kyiv")
        city2 = sample_city(country=country, name="Lviv")

        airport = sample_airport(city=city)
        airport2 = sample_airport(
            name="Lviv International Airport", iata_code="LWO", city=city2
        )

        response = self.client.get(AIRPORT_URL, {"city": city.id})

        serializer = AirportListSerializer(airport)
        serializer2 = AirportListSerializer(airport2)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(serializer.data, response.data["results"])
        self.assertNotIn(serializer2.data, response.data["results"])


class AdminAirportAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com",
            password="test123",
            is_staff=True,
        )
        self.client.force_authenticate(self.user)

    def test_create_airport(self):
        city = sample_city()

        payload = {
            "name": "Boryspil International Airport",
            "city": city.id,
            "iata_code": "KBP",
        }

        response = self.client.post(AIRPORT_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Airport.objects.filter(
                name="Boryspil International Airport",
                city=city,
                iata_code="KBP"
            ).exists()
        )

    def test_update_airport(self):
        airport = sample_airport()

        payload = {"name": "New Airport Name"}

        response = self.client.patch(detail_url(airport.id), payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        airport.refresh_from_db()

        self.assertEqual(airport.name, payload["name"])

    def test_delete_airport(self):
        airport = sample_airport()

        response = self.client.delete(detail_url(airport.id))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertFalse(Airport.objects.filter(id=airport.id).exists())

    def test_airport_image_upload(self):
        airport = sample_airport()

        image = Image.new("RGB", (100, 100))
        image_file = BytesIO()
        image.save(image_file, format="JPEG")
        image_file.seek(0)

        image = SimpleUploadedFile(
            "airport.jpg",
            image_file.read(),
            content_type="image/jpeg",
        )

        response = self.client.post(
            detail_url(airport.id) + "upload-image/",
            {"airport_image": image},
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        airport.refresh_from_db()

        self.assertTrue(airport.airport_image)
