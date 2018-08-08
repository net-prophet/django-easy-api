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


# Test the common route debug which just gives full api access to anyone
class DebugAPITests(APITestCase):
    def setUp(self):
        # Set up the DB
        for color, size, shape in itertools.product(COLORS, SIZES, SHAPES):
            Widget.objects.create(color=color[0],
                                  size=size[0],
                                  shape=shape[0])

        for i in range(0, 200):
            PurchaseFactory.create()

        # Let's create a test user and set our client
        self.client = APIClient()

    def test_getting_root(self):
        self.client.get('/')

    def test_debug_root(self):
        response = self.client.get('/debugapi/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_debug_get_widget(self):
        widgets = self.client.get('/debugapi/widgets/')
        self.assertEqual(widgets.status_code, status.HTTP_200_OK)

        self.assertEqual(len(widgets.data), 336)
        rand_index = random.randint(0, len(widgets.data) - 1)
        widget_fields = ['id', 'name', 'color', 'size', 'shape', 'cost']

        self.assertEqual(len(widgets.data[rand_index]), len(widget_fields))
        [self.assertIn(field, widgets.data[rand_index])
         for field in widget_fields]

    def test_debug_get_purchases(self):
        purchases = self.client.get('/debugapi/purchases/')
        self.assertEqual(purchases.status_code, status.HTTP_200_OK)

        self.assertEqual(len(purchases.data), 200)
        rand_index = random.randint(0, len(purchases.data) - 1)
        purchase_fields = ['id', 'sale_date', 'sale_price', 'profit',
                           'customer', 'items']

        self.assertEqual(len(purchases.data[rand_index]), len(purchase_fields))
        [self.assertIn(field, purchases.data[rand_index])
         for field in purchase_fields]

    def test_debug_get_customers(self):
        customers = self.client.get('/debugapi/customers/')
        self.assertEqual(customers.status_code, status.HTTP_200_OK)

        self.assertEqual(len(customers.data), 200)
        rand_index = random.randint(0, len(customers.data) - 1)
        customer_fields = ['id', 'name', 'state', 'gender', 'age']

        self.assertEqual(len(customers.data[rand_index]), len(customer_fields))
        [self.assertIn(field, customers.data[rand_index])
         for field in customer_fields]


# Test the common adminapi which just gives full api access to admins only
class AdminAPITest(APITestCase):
    def setUp(self):
        # Set up the DB
        for color, size, shape in itertools.product(COLORS, SIZES, SHAPES):
            Widget.objects.create(color=color[0],
                                  size=size[0],
                                  shape=shape[0])

        for i in range(0, 200):
            PurchaseFactory.create()

        # Let's create a test user and set our client
        self.client = APIClient()
        self.user = User.objects.create_superuser(username=SUPER['username'],
                                                  email=SUPER['email'],
                                                  password=SUPER['password'])
        self.user.save()

    def test_admin_root(self):
        response = self.client.get('/adminapi/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_get_widget(self):
        widgets = self.client.get('/adminapi/widgets/')
        self.assertEqual(widgets.status_code, status.HTTP_403_FORBIDDEN)
        self.client.login(username=SUPER['username'],
                          password=SUPER['password'])
        widgets = self.client.get('/adminapi/widgets/')
        self.assertEqual(widgets.status_code, status.HTTP_200_OK)

        self.assertEqual(len(widgets.data), 336)
        rand_index = random.randint(0, len(widgets.data) - 1)
        widget_fields = ['id', 'name', 'color', 'size', 'shape', 'cost']

        self.assertEqual(len(widgets.data[rand_index]), len(widget_fields))
        [self.assertIn(field, widgets.data[rand_index])
         for field in widget_fields]

    def test_admin_get_purchases(self):
        purchases = self.client.get('/adminapi/purchases/')
        self.assertEqual(purchases.status_code, status.HTTP_403_FORBIDDEN)
        self.client.login(username=SUPER['username'],
                          password=SUPER['password'])
        purchases = self.client.get('/adminapi/purchases/')
        self.assertEqual(purchases.status_code, status.HTTP_200_OK)

        self.assertEqual(len(purchases.data), 200)
        rand_index = random.randint(0, len(purchases.data) - 1)
        purchase_fields = ['id', 'sale_date', 'sale_price', 'profit',
                           'customer', 'items']

        self.assertEqual(len(purchases.data[rand_index]), len(purchase_fields))
        [self.assertIn(field, purchases.data[rand_index])
         for field in purchase_fields]

    def test_admin_get_customers(self):
        customers = self.client.get('/adminapi/customers/')
        self.assertEqual(customers.status_code, status.HTTP_403_FORBIDDEN)
        self.client.login(username=SUPER['username'],
                          password=SUPER['password'])
        customers = self.client.get('/adminapi/customers/')
        self.assertEqual(customers.status_code, status.HTTP_200_OK)

        self.assertEqual(len(customers.data), 200)
        rand_index = random.randint(0, len(customers.data) - 1)
        customer_fields = ['id', 'name', 'state', 'gender', 'age']

        self.assertEqual(len(customers.data[rand_index]), len(customer_fields))
        [self.assertIn(field, customers.data[rand_index])
         for field in customer_fields]


class PublicAPITest(APITestCase):
    def setUp(self):
        # Set up the DB
        for color, size, shape in itertools.product(COLORS, SIZES, SHAPES):
            Widget.objects.create(color=color[0],
                                  size=size[0],
                                  shape=shape[0])

        for i in range(0, 200):
            PurchaseFactory.create()

        # Let's create a test user and set our client
        self.client = APIClient()

    def test_public_root(self):
        response = self.client.get('/publicapi/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_public_get_widget(self):
        widgets = self.client.get('/publicapi/widgets/')
        self.assertEqual(widgets.status_code, status.HTTP_200_OK)

        self.assertEqual(len(widgets.data), 336)
        rand_index = random.randint(0, len(widgets.data) - 1)
        widget_fields = ['name', 'color']

        self.assertEqual(len(widgets.data[rand_index]), len(widget_fields))
        [self.assertIn(field, widgets.data[rand_index])
         for field in widget_fields]

    def test_public_get_purchases(self):
        purchases = self.client.get('/publicapi/purchases/')
        self.assertEqual(purchases.status_code, status.HTTP_200_OK)

        self.assertEqual(len(purchases.data), 200)
        rand_index = random.randint(0, len(purchases.data) - 1)
        purchase_fields = ['items', 'sale_price']

        self.assertEqual(len(purchases.data[rand_index]), len(purchase_fields))
        [self.assertIn(field, purchases.data[rand_index])
         for field in purchase_fields]

    def test_public_get_customers(self):
        customers = self.client.get('/publicapi/customers/')
        self.assertEqual(customers.status_code, status.HTTP_200_OK)

        self.assertEqual(len(customers.data), 200)
        rand_index = random.randint(0, len(customers.data) - 1)
        customer_fields = ['name', 'age']

        self.assertEqual(len(customers.data[rand_index]), len(customer_fields))
        [self.assertIn(field, customers.data[rand_index])
         for field in customer_fields]


# For this you get full API access but only if logged in
class PrivateAPITest(APITestCase):
    def setUp(self):
        # Set up the DB
        for color, size, shape in itertools.product(COLORS, SIZES, SHAPES):
            Widget.objects.create(color=color[0],
                                  size=size[0],
                                  shape=shape[0])

        for i in range(0, 200):
            PurchaseFactory.create()

        # Let's create a test user and set our client
        self.client = APIClient()
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
        widget_fields = ['name', 'color', 'size', 'shape', 'cost']

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
                           'customer', 'items']

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
        customer_fields = ['name', 'state', 'gender', 'age']

        self.assertEqual(len(customers.data[rand_index]), len(customer_fields))
        [self.assertIn(field, customers.data[rand_index])
         for field in customer_fields]
