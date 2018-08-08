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
