from django.contrib.auth import get_user_model
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.reverse import reverse

from airport.models import Country
from airport.serializers import CountryListAndRetrieveSerializer

COUNTRY_URL = reverse("airport:country-list")


def detail_url(country_id):
    return reverse("airport:country-detail", args=(country_id,))


def sample_country(**params) -> Country:
    defaults = {"name": "Ukraine"}
    defaults.update(params)
    return Country.objects.create(**defaults)


class UnauthenticatedCountryAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        response = self.client.get(COUNTRY_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedCountryAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com", password="test123"
        )
        self.client.force_authenticate(self.user)

    def test_country_list(self):
        sample_country()
        sample_country(name="Germany")
        response = self.client.get(COUNTRY_URL)
        countries = Country.objects.all()
        serializer = CountryListAndRetrieveSerializer(countries, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], serializer.data)

    def test_country_retrieve(self):
        country = sample_country()
        url = detail_url(country.id)
        response = self.client.get(url)
        serializer = CountryListAndRetrieveSerializer(country)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_create_country_forbidden(self):
        payload = {"name": "Ukraine"}
        response = self.client.post(COUNTRY_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_country_forbidden(self):
        country = sample_country()
        payload = {"name": "Germany"}
        response = self.client.patch(detail_url(country.id), payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_country_forbidden(self):
        country = sample_country()
        response = self.client.delete(detail_url(country.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_country_image_upload_forbidden(self):
        country = sample_country()

        image = Image.new("RGB", (100, 100))
        image_file = BytesIO()
        image.save(image_file, format="JPEG")
        image_file.seek(0)

        flag = SimpleUploadedFile(
            "flag.jpg",
            image_file.read(),
            content_type="image/jpeg",
        )

        response = self.client.post(
            detail_url(country.id) + "upload-image/",
            {"country_flag": flag},
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_search_country_by_name(self):
        country = sample_country()
        country2 = sample_country(name="Germany")

        response = self.client.get(COUNTRY_URL, {"search": "Ukr"})

        serializer = CountryListAndRetrieveSerializer(country)
        serializer2 = CountryListAndRetrieveSerializer(country2)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(serializer.data, response.data["results"])
        self.assertNotIn(serializer2.data, response.data["results"])

    def test_ordering_country_by_name(self):
        sample_country()
        sample_country(name="Germany")
        sample_country(name="France")

        response = self.client.get(COUNTRY_URL, {"ordering": "name"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        names = [country["name"] for country in response.data["results"]]

        self.assertEqual(names, ["France", "Germany", "Ukraine"])

    def test_ordering_country_by_name_descending(self):
        sample_country()
        sample_country(name="Germany")
        sample_country(name="France")

        response = self.client.get(COUNTRY_URL, {"ordering": "-name"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        names = [country["name"] for country in response.data["results"]]

        self.assertEqual(names, ["Ukraine", "Germany", "France"])


class AdminCountryAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com",
            password="test123",
            is_staff=True,
        )
        self.client.force_authenticate(self.user)

    def test_create_country(self):
        payload = {"name": "Ukraine"}
        response = self.client.post(COUNTRY_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Country.objects.filter(name="Ukraine").exists())

    def test_update_country(self):
        country = sample_country()
        payload = {"name": "Germany"}
        response = self.client.patch(detail_url(country.id), payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        country.refresh_from_db()
        self.assertEqual(country.name, payload["name"])

    def test_delete_country(self):
        country = sample_country()
        response = self.client.delete(detail_url(country.id))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Country.objects.filter(id=country.id).exists())

    def test_country_image_upload(self):
        country = sample_country()

        image = Image.new("RGB", (100, 100))
        image_file = BytesIO()
        image.save(image_file, format="JPEG")
        image_file.seek(0)

        flag = SimpleUploadedFile(
            "flag.jpg",
            image_file.read(),
            content_type="image/jpeg",
        )

        response = self.client.post(
            detail_url(country.id) + "upload-image/",
            {"country_flag": flag},
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        country.refresh_from_db()

        self.assertTrue(country.country_flag)
