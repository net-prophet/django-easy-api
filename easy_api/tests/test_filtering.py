import itertools
from rest_framework import status
from widgets.models import Widget
from widgets.options import COLORS, SIZES, SHAPES
from tests.factories import PurchaseFactory
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient

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


class FilteringTest(APITestCase):
    def setUp(self):
        self.client = APIClient()

    @classmethod
    def setUpClass(self):
        # Set up the DB
        super(FilteringTest, self).setUpClass()
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

        # Also, a superuser
        self.suser = User.objects.create_superuser(
            username=SUPER['username'],
            email=SUPER['email'],
            password=SUPER['password']
        )
        self.suser.save()

    def test_filtering_widgets(self):
        api_widgets = self.client.get('/publicapi/widgets/')
        widgets = Widget.objects.all()
        self.assertEqual(api_widgets.status_code, status.HTTP_200_OK)
        self.assertEqual(len(api_widgets.data), widgets.count())
        for c in COLORS:
            url = '/publicapi/widgets/?color=%s' % c[0]
            api_widgets = self.client.get(url)
            widgets = Widget.objects.all().filter(color=c[0])
            self.assertEqual(api_widgets.status_code, status.HTTP_200_OK)
            self.assertEqual(len(api_widgets.data), widgets.count())

        # Lets login to filter private fields
        self.client.login(username=TEST['username'],
                          password=TEST['password'])

        for color, size, shape in itertools.product(COLORS, SIZES, SHAPES):
            fields = (color[0], size[0], shape[0])
            url = '/privateapi/widgets/?color=%s&size=%s&shape=%s' % fields
            api_widgets = self.client.get(url)
            widgets = Widget.objects.all().filter(color=color[0],
                                                  size=size[0],
                                                  shape=shape[0]
                                                  )
            self.assertEqual(api_widgets.status_code, status.HTTP_200_OK)
            self.assertEqual(len(api_widgets.data), widgets.count())
