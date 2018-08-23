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


class PermissionsAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()

    @classmethod
    def setUpClass(self):
        # Set up the DB
        super(PermissionsAPITest, self).setUpClass()
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

    def test_root(self):
        response = self.client.get('/complexapi/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # Permissions to create and delete a widget are admin only
    def test_create_and_delete_widget(self):

        # So we can't create not logged in
        widgets = self.client.get('/complexapi/widgets/')
        self.assertEqual(widgets.status_code, status.HTTP_403_FORBIDDEN)

        # Now lets make sure being authenticated isn't enough
        self.client.login(username=TEST['username'],
                          password=TEST['password'])
        widgets = self.client.get('/complexapi/widgets/')
        self.assertEqual(widgets.status_code, status.HTTP_200_OK)
        create = {'name': 'test_widget',
                  'color': 'blue',
                  'size': 'large',
                  'shape': 'circle'}
        response = self.client.post('/complexapi/widgets/', data=create)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Finally, a superuser should be successful
        self.client.login(username=SUPER['username'],
                          password=SUPER['password'])
        response = self.client.post('/complexapi/widgets/', data=create)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # OK now lets delete this bad boy, also admin user
        '''
        delete_me = self.client.get('/complexapi/widgets/?name=test_widget')
        print('deleteme data: ', delete_me)
        print('deleteme data: ', delete_me.data)
        deleted = self.client.delete('/complexapi/widgets/?name=test_widget',
                                     data=delete_me)
        print('deleteme: ', deleted)
        print('deleteme data: ', deleted.data)
        print('deleteme data: ', deleted.context_data)
        print('deleteme data: ', deleted.context)
        self.assertEqual(delete_me.status_code, status.HTTP_200_OK)
        '''

    # Permissions to list widgets is IsAuthenticated
    def test_list_widget(self):

        # So should fail here
        widgets = self.client.get('/complexapi/widgets/')
        self.assertEqual(widgets.status_code, status.HTTP_403_FORBIDDEN)

        # But lets login and try
        self.client.login(username=TEST['username'],
                          password=TEST['password'])
        widgets = self.client.get('/complexapi/widgets/')
        self.assertEqual(widgets.status_code, status.HTTP_200_OK)

        # This makes sure we got all of the results
        self.assertEqual(len(widgets.data), 336)

        # Then we randomly pick one to make sure the fields are present
        rand_index = random.randint(0, len(widgets.data) - 1)
        widget_fields = ['name', 'color', 'size', 'shape', 'cost']
        self.assertEqual(len(widgets.data[rand_index]), len(widget_fields))
        [self.assertIn(field, widgets.data[rand_index])
         for field in widget_fields]

    # Permissions to retrieve widgets are AllowAny
    def test_retrieve_widget(self):

        # So should fail here
        rand_index = random.randint(1, 336)
        url = '/complexapi/widgets/' + str(rand_index) + '/'
        widgets = self.client.get(url)
        self.assertEqual(widgets.status_code, status.HTTP_200_OK)

        widget_fields = ['name', 'color', 'size', 'shape', 'cost']
        self.assertEqual(len(widgets.data), len(widget_fields))
        [self.assertIn(field, widgets.data)
         for field in widget_fields]
