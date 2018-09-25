import itertools
from rest_framework import status
from widgets.models import Widget
from widgets.options import COLORS, SIZES, SHAPES
from tests.factories import PurchaseFactory
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
import random

User = get_user_model()

TEST = {
    'username': 'testuser',
    'email': 'test@test.co',
    'password': 'testing123'
}

SUPER = {
    'username': 'testsuper',
    'email': 'super@test.co',
    'password': 'super123'
}


class PublicAPITest(APITestCase):
    def setUp(self):
        # Let's create a test user and set our client
        self.client = APIClient()

    @classmethod
    def setUpClass(cls):
        # Set up the DB
        super(PublicAPITest, cls).setUpClass()
        for color, size, shape in itertools.product(COLORS, SIZES, SHAPES):
            Widget.objects.create(color=color[0],
                                  size=size[0],
                                  shape=shape[0])

        for i in range(0, 200):
            PurchaseFactory.create()

    def test_public_root(self):
        response = self.client.get('/publicapi/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_public_metadata(self):
        response = self.client.options('/publicapi/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn('name', response.data)
        self.assertEqual(response.data['name'], 'Public API')
        self.assertIn('description', response.data)
        description = 'This is a public API'
        self.assertEqual(response.data['description'], description)
        self.assertIn('actions', response.data)

    def test_model_metadata(self):
        response = self.client.options('/publicapi/widgets/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn('name', response.data)
        self.assertEqual(response.data['name'], 'Widgets')
        self.assertIn('description', response.data)
        description = 'Generated by EasyAPI'
        self.assertEqual(response.data['description'], description)
        self.assertIn('actions', response.data)
        self.assertIn('filters', response.data)

        # Test that None has_permission is False (always returns False)
        # This is PURELY to get to 100% test coverage, it's a dumb test
        from EasyAPI.models import ModelAPI
        self.assertFalse(ModelAPI.AllowNone.has_permission(None, None, None))

    def test_public_get_widget(self):
        widgets = self.client.get('/publicapi/widgets/')
        self.assertEqual(widgets.status_code, status.HTTP_200_OK)

        self.assertEqual(len(widgets.data), 336)
        rand_index = random.randint(0, len(widgets.data) - 1)
        widget_fields = ['name', 'color', 'pk']

        self.assertEqual(len(widgets.data[rand_index]), len(widget_fields))
        [self.assertIn(field, widgets.data[rand_index])
         for field in widget_fields]

    def test_public_get_purchases(self):
        purchases = self.client.get('/publicapi/purchases/')
        self.assertEqual(purchases.status_code, status.HTTP_200_OK)

        self.assertEqual(len(purchases.data), 200)
        rand_index = random.randint(0, len(purchases.data) - 1)
        purchase_fields = ['items', 'sale_price', 'pk']

        self.assertEqual(len(purchases.data[rand_index]), len(purchase_fields))
        [self.assertIn(field, purchases.data[rand_index])
         for field in purchase_fields]

    def test_public_get_customers(self):
        customers = self.client.get('/publicapi/customers/')
        self.assertEqual(customers.status_code, status.HTTP_200_OK)

        self.assertEqual(len(customers.data), 200)
        rand_index = random.randint(0, len(customers.data) - 1)
        customer_fields = ['name', 'age', 'pk']

        self.assertEqual(len(customers.data[rand_index]), len(customer_fields))
        [self.assertIn(field, customers.data[rand_index])
         for field in customer_fields]


# For this you get full API access but only if logged in
class PrivateAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()

    @classmethod
    def setUpClass(self):
        # Set up the DB
        super(PrivateAPITest, self).setUpClass()
        for color, size, shape in itertools.product(COLORS, SIZES, SHAPES):
            Widget.objects.create(color=color[0],
                                  size=size[0],
                                  shape=shape[0])

        for i in range(0, 200):
            PurchaseFactory.create()

        # Let's create a test user and set our client
        self.user = User.objects.create(username=TEST['username'],
                                        email=TEST['email'])
        self.user.set_password(TEST['password'])
        self.user.save()

    def test_private_root(self):
        response = self.client.get('/privateapi/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_private_get_widget(self):
        widgets = self.client.get('/privateapi/widgets/')
        self.assertEqual(widgets.status_code, status.HTTP_403_FORBIDDEN)
        self.client.login(username=TEST['username'],
                          password=TEST['password'])
        widgets = self.client.get('/privateapi/widgets/')
        self.assertEqual(widgets.status_code, status.HTTP_200_OK)

        self.assertEqual(len(widgets.data), 336)
        rand_index = random.randint(0, len(widgets.data) - 1)
        widget_fields = ['name', 'color', 'size', 'shape', 'cost', 'pk']

        self.assertEqual(len(widgets.data[rand_index]), len(widget_fields))
        [self.assertIn(field, widgets.data[rand_index])
         for field in widget_fields]

    def test_private_get_purchases(self):
        purchases = self.client.get('/privateapi/purchases/')
        self.assertEqual(purchases.status_code, status.HTTP_403_FORBIDDEN)
        self.client.login(username=TEST['username'],
                          password=TEST['password'])
        purchases = self.client.get('/privateapi/purchases/')
        self.assertEqual(purchases.status_code, status.HTTP_200_OK)

        self.assertEqual(len(purchases.data), 200)
        rand_index = random.randint(0, len(purchases.data) - 1)
        purchase_fields = ['sale_date', 'sale_price', 'profit',
                           'customer', 'items', 'pk']

        self.assertEqual(len(purchases.data[rand_index]), len(purchase_fields))
        [self.assertIn(field, purchases.data[rand_index])
         for field in purchase_fields]

    def test_private_get_customers(self):
        customers = self.client.get('/privateapi/customers/')
        self.assertEqual(customers.status_code, status.HTTP_403_FORBIDDEN)
        self.client.login(username=TEST['username'],
                          password=TEST['password'])
        customers = self.client.get('/privateapi/customers/')
        self.assertEqual(customers.status_code, status.HTTP_200_OK)

        self.assertEqual(len(customers.data), 200)
        rand_index = random.randint(0, len(customers.data) - 1)
        customer_fields = ['name', 'state', 'gender', 'age', 'pk']

        self.assertEqual(len(customers.data[rand_index]), len(customer_fields))
        [self.assertIn(field, customers.data[rand_index])
         for field in customer_fields]
