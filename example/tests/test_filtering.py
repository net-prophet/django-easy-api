import itertools

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from example.app.widgets.models import Store, Widget
from example.app.widgets.options import COLORS, SHAPES, SIZES
from example.tests.factories import PurchaseFactory

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

# This will be the number of colors, sizes and shapes to permutate
# Setting this value higher causes exponential slowness, but can be used to verify test correctness
NUM_OPTS=3 

# This used to be 200 but 50 is giving just as good of answers
NUM_PURCHASES=50

class FilteringTest(APITestCase):
    def setUp(self):
        self.client = APIClient()

    @classmethod
    def setUpClass(self):
        # Set up the DB
        super(FilteringTest, self).setUpClass()
        self.all_options = lambda *_: itertools.product(COLORS[:NUM_OPTS], SIZES[:NUM_OPTS], SHAPES[:NUM_OPTS])
        for color, size, shape in self.all_options():
            Widget.objects.create(color=color[0],
                                  size=size[0],
                                  shape=shape[0])

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
                          
        Store.objects.update(owner=self.user)

        for color, size, shape in self.all_options():
            fields = (color[0], size[0], shape[0])
            url = '/privateapi/widgets/?color=%s&size=%s&shape=%s' % fields
            api_widgets = self.client.get(url)
            widgets = Widget.objects.all().filter(color=color[0],
                                                  size=size[0],
                                                  shape=shape[0]
                                                  )
            self.assertEqual(api_widgets.status_code, status.HTTP_200_OK)
            self.assertEqual(len(api_widgets.data), widgets.count())
