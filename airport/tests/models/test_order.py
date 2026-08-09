from django.contrib.auth import get_user_model
from django.test import TestCase

from airport.models import Order


class OrderTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="test@test.com",
            password="test123"
        )
        self.order = Order.objects.create(
            user=self.user,
        )

    def test_str(self):
        self.assertEqual(
            str(self.order),
            f"Order #{self.order.id} ({self.user.email})"
        )

    def test_order_belongs_to_user(self):
        self.assertEqual(self.order.user, self.user)
