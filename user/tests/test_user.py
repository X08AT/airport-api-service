from django.test import TestCase
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from user.models import User


REGISTER_URL = reverse("user:create")
LOGIN_URL = reverse("user:token_obtain_pair")
MANAGE_URL = reverse("user:manage")


def sample_user(**params) -> User:
    defaults = {
        "email": "test@mail.com",
        "password": "test123",
    }
    defaults.update(params)
    return User.objects.create_user(**defaults)


class TestUser(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_user(self):
        payload = {
            "email": "test@mail.com",
            "password": "test123",
        }
        response = self.client.post(REGISTER_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email="test@mail.com").exists())

    def test_register_user_invalid_password(self):
        payload = {
            "email": "test@mail.com",
            "password": "test",
        }
        response = self.client.post(REGISTER_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(email="test@mail.com").exists())

    def test_register_user_duplicate_email(self):
        sample_user()
        payload = {
            "email": "test@mail.com",
            "password": "test123",
        }
        response = self.client.post(REGISTER_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_user(self):
        sample_user()
        payload = {
            "email": "test@mail.com",
            "password": "test123",
        }
        response = self.client.post(LOGIN_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_login_user_invalid_password(self):
        sample_user()
        payload = {
            "email": "test@mail.com",
            "password": "123test",
        }
        response = self.client.post(LOGIN_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_user_invalid_email(self):
        sample_user()
        payload = {
            "email": "abc@mail.com",
            "password": "test123",
        }
        response = self.client.post(LOGIN_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_profile(self):
        user = sample_user()
        self.client.force_authenticate(user)

        response = self.client.get(MANAGE_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], user.email)

    def test_user_profile_unauthorized(self):
        response = self.client.get(MANAGE_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_profile_change_email(self):
        user = sample_user()
        self.client.force_authenticate(user)

        payload = {
            "email": "abc@mail.com",
        }

        response = self.client.patch(MANAGE_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertEqual(response.data["email"], user.email)

    def test_user_profile_change_password(self):
        user = sample_user()
        self.client.force_authenticate(user)

        payload = {
            "password": "123test",
        }

        response = self.client.patch(MANAGE_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.check_password("123test"))
