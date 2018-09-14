import itertools
from rest_framework import status
from django.test import modify_settings
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

    def test_root(self):
        response = self.client.get('/complexapi/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # Import the APIs that we have registered then try to hit their roots
    def test_autodiscover(self):
        api_names = ['Public API', 'Private API', 'Complex API']
        from EasyAPI.models import all_apis
        for api in all_apis:
            self.assertIn(api.name, api_names)

    def test_apps_installed(self):
        from django.apps import apps
        from EasyAPI.models import EasyAPI
        app_config = set(apps.get_app_configs())
        self.assertEqual(EasyAPI.check_dependencies(app_config), [])

    def test_register_abstract_model(self):
        from django.db import models
        from EasyAPI.models import ModelAPI

        class AbstractModel(models.Model):

            class Meta:
                abstract = True

        class AbstractModelAPI(ModelAPI):
            pass

        from easy_api.api import complexapi
        from django.core.exceptions import ImproperlyConfigured
        with self.assertRaises(ImproperlyConfigured):
            complexapi.register(AbstractModel, AbstractModelAPI)

    def test_register_object_not_modelapi_subclass(self):

        class NotAModelAPI(object):
            pass

        from widgets.models import Widget
        from easy_api.api import complexapi
        from django.core.exceptions import ImproperlyConfigured
        with self.assertRaises(ImproperlyConfigured):
            complexapi.register(Widget, NotAModelAPI)

    def test_register_model_twice(self):
        from widgets.models import Widget
        from easy_api.api import complexapi
        from widgets.api import ComplexWidgetAPI
        from EasyAPI.models import AlreadyRegistered
        with self.assertRaises(AlreadyRegistered):
            complexapi.register(Widget, ComplexWidgetAPI)

    @modify_settings(INSTALLED_APPS={'remove': ['EasyAPI']})
    def test_checking_easyapi_installed(self):
        from django.apps import apps
        from EasyAPI.models import EasyAPI
        app_config = set(apps.get_app_configs())
        self.assertEqual(EasyAPI.check_dependencies(app_config), [])

    @modify_settings(INSTALLED_APPS={'remove': ['rest_framework']})
    def test_checking_drf_installed(self):
        from django.apps import apps
        from EasyAPI.models import EasyAPI
        from django.core.checks import Error
        app = 'rest_framework'
        expected = [
            Error(
                "'%s' must be in INSTALLED_APPS to use django-easy-api" % app
            )
        ]
        app_config = set(apps.get_app_configs())
        error = EasyAPI.check_dependencies(app_config)
        self.assertEqual(error, expected)

    @modify_settings(INSTALLED_APPS={'remove': ['django_filters']})
    def test_checking_django_filters_installed(self):
        from django.apps import apps
        from EasyAPI.models import EasyAPI
        from django.core.checks import Error
        app = 'django_filters'
        expected = [
            Error(
                "'%s' must be in INSTALLED_APPS to use django-easy-api" % app
            )
        ]
        app_config = set(apps.get_app_configs())
        error = EasyAPI.check_dependencies(app_config)
        self.assertEqual(error, expected)

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

        # Let's check that we can retrieve what we just created
        delete_me = self.client.get('/complexapi/widgets/?name=test_widget')
        for k, v in create.items():
            self.assertEqual(delete_me.data[0][k], v)

        # Bulk delete not available this should fail
        deleted = self.client.delete('/complexapi/widgets/?color=red')
        self.assertEqual(deleted.status_code, status.HTTP_403_FORBIDDEN)

        # Deleting something that doesn't exist
        deleted = self.client.delete('/complexapi/widgets/?name=peter')
        self.assertEqual(deleted.status_code, status.HTTP_404_NOT_FOUND)

        # Let's actually delete this time
        deleted = self.client.delete('/complexapi/widgets/?name=test_widget')
        self.assertEqual(deleted.status_code, status.HTTP_204_NO_CONTENT)

        # Let's check that we can retrieve what we just created
        deleted = self.client.get('/complexapi/widgets/?name=test_widget')
        self.assertEqual(deleted.status_code, status.HTTP_200_OK)
        self.assertEqual(deleted.data, [])

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
