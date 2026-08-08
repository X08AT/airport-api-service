from django.contrib.auth import get_user_model
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.reverse import reverse

from airport.models import Country, City
from airport.serializers import CityListSerializer, CityDetailSerializer

CITY_URL = reverse("airport:city-list")


def detail_url(city_id):
    return reverse("airport:city-detail", args=(city_id,))


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


class UnauthenticatedCityAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        response = self.client.get(CITY_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedCityAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com", password="test123"
        )
        self.client.force_authenticate(self.user)

    def test_city_list(self):
        country = sample_country()
        sample_city(country=country)
        sample_city(name="Lviv", country=country)

        response = self.client.get(CITY_URL)

        cities = City.objects.all()
        serializer = CityListSerializer(cities, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], serializer.data)

    def test_city_retrieve(self):
        city = sample_city()
        url = detail_url(city.id)

        response = self.client.get(url)
        serializer = CityDetailSerializer(city)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_create_city_forbidden(self):
        country = sample_country()

        payload = {
            "name": "Lviv",
            "country": country.id,
        }

        response = self.client.post(CITY_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_city_forbidden(self):
        city = sample_city()

        payload = {
            "name": "Lviv",
        }

        response = self.client.patch(detail_url(city.id), payload)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_city_forbidden(self):
        city = sample_city()

        response = self.client.delete(detail_url(city.id))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_city_image_upload_forbidden(self):
        city = sample_city()

        image = Image.new("RGB", (100, 100))
        image_file = BytesIO()
        image.save(image_file, format="JPEG")
        image_file.seek(0)

        image = SimpleUploadedFile(
            "city.jpg",
            image_file.read(),
            content_type="image/jpeg",
        )

        response = self.client.post(
            detail_url(city.id) + "upload-image/",
            {"city_image": image},
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_search_city_by_name(self):
        country = sample_country()

        city = sample_city(country=country)
        city2 = sample_city(name="Lviv", country=country)

        response = self.client.get(CITY_URL, {"search": "Kyiv"})

        serializer = CityListSerializer(city)
        serializer2 = CityListSerializer(city2)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(serializer.data, response.data["results"])
        self.assertNotIn(serializer2.data, response.data["results"])

    def test_ordering_city_by_name(self):
        country = sample_country()

        sample_city(country=country, name="Kyiv")
        sample_city(country=country, name="Lviv")
        sample_city(country=country, name="Odesa")

        response = self.client.get(CITY_URL, {"ordering": "name"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        names = [city["name"] for city in response.data["results"]]

        self.assertEqual(names, ["Kyiv", "Lviv", "Odesa"])

    def test_ordering_city_by_name_descending(self):
        country = sample_country()

        sample_city(country=country, name="Kyiv")
        sample_city(country=country, name="Lviv")
        sample_city(country=country, name="Odesa")

        response = self.client.get(CITY_URL, {"ordering": "-name"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        names = [city["name"] for city in response.data["results"]]

        self.assertEqual(names, ["Odesa", "Lviv", "Kyiv"])

    def test_filter_city_by_country(self):
        country = sample_country()
        country2 = sample_country(name="Poland")

        city = sample_city(country=country)
        city2 = sample_city(name="Krakow", country=country2)

        response = self.client.get(CITY_URL, {"country": country.id})

        serializer = CityListSerializer(city)
        serializer2 = CityListSerializer(city2)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(serializer.data, response.data["results"])
        self.assertNotIn(serializer2.data, response.data["results"])


class AdminCityAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com",
            password="test123",
            is_staff=True,
        )
        self.client.force_authenticate(self.user)

    def test_create_city(self):
        country = sample_country()

        payload = {
            "name": "Kyiv",
            "country": country.id,
        }

        response = self.client.post(CITY_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            City.objects.filter(
                name="Kyiv", country=country
            ).exists()
        )

    def test_update_city(self):
        city = sample_city()

        payload = {"name": "Lviv"}

        response = self.client.patch(detail_url(city.id), payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        city.refresh_from_db()

        self.assertEqual(city.name, payload["name"])

    def test_delete_city(self):
        city = sample_city()

        response = self.client.delete(detail_url(city.id))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertFalse(City.objects.filter(id=city.id).exists())

    def test_city_image_upload(self):
        city = sample_city()

        image = Image.new("RGB", (100, 100))
        image_file = BytesIO()
        image.save(image_file, format="JPEG")
        image_file.seek(0)

        image = SimpleUploadedFile(
            "city.jpg",
            image_file.read(),
            content_type="image/jpeg",
        )

        response = self.client.post(
            detail_url(city.id) + "upload-image/",
            {"city_image": image},
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        city.refresh_from_db()

        self.assertTrue(city.city_image)
