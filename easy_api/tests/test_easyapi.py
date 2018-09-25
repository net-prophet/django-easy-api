import itertools
from rest_framework import status
from django.test import modify_settings
from widgets.models import Widget
from widgets.options import COLORS, SIZES, SHAPES
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


class APIMethodsTest(APITestCase):
    def setUp(self):
        self.client = APIClient()

    @classmethod
    def setUpClass(self):
        # Set up the DB
        super(APIMethodsTest, self).setUpClass()
        for color, size, shape in itertools.product(COLORS, SIZES, SHAPES):
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

        # Let's retrieve it with our filters
        filtered = self.client.get('/complexapi/widgets/?name=test_widget')
        for k, v in create.items():
            self.assertEqual(filtered.data[0][k], v)

        # Let's check that we can retrieve what we just created
        pk = response.data['pk']
        url = '/complexapi/widgets/%s/' % str(pk)
        delete_me = self.client.get(url)
        for k, v in create.items():
            self.assertEqual(delete_me.data[k], v)

        # Delete it
        deleted = self.client.delete(url)
        self.assertEqual(deleted.status_code, status.HTTP_204_NO_CONTENT)

        # Check if its deleted
        deleted = self.client.delete(url)
        self.assertEqual(deleted.status_code, status.HTTP_404_NOT_FOUND)

        # Check if its deleted via filter
        filtered_del = self.client.get('/complexapi/widgets/?name=test_widget')
        self.assertEqual(filtered_del.status_code, status.HTTP_200_OK)
        self.assertEqual(filtered_del.data, [])

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
        widget_fields = ['name', 'color', 'size', 'shape', 'cost', 'pk']
        self.assertEqual(len(widgets.data[rand_index]), len(widget_fields))
        [self.assertIn(field, widgets.data[rand_index])
         for field in widget_fields]

    # Permissions to retrieve widgets are AllowAny
    def test_retrieve_widget(self):

        rand_index = random.randint(1, 336)
        url = '/complexapi/widgets/%s/'
        widgets = self.client.get(url % str(rand_index))
        self.assertEqual(widgets.status_code, status.HTTP_200_OK)

        pk = widgets.data['pk']
        self.assertEqual(pk, rand_index)
        widgets_from_pk = self.client.get(url % str(pk))
        self.assertEqual(widgets.data, widgets_from_pk.data)

        widget_fields = ['name', 'color', 'size', 'shape', 'cost', 'pk']
        self.assertEqual(len(widgets.data), len(widget_fields))
        [self.assertIn(field, widgets.data)
         for field in widget_fields]

    def test_update_widget(self):

        rand_index = random.randint(1, 336)
        url = '/complexapi/widgets/%s/'
        widgets = self.client.get(url % str(rand_index))
        self.assertEqual(widgets.status_code, status.HTTP_200_OK)

        name = {'name': 'changed_name'}
        changed = self.client.patch(url % str(widgets.data['pk']), data=name)
        self.assertEqual(changed.status_code, status.HTTP_200_OK)

        changed_get = self.client.get(url % str(changed.data['pk']))
        self.assertEqual(changed_get.status_code, status.HTTP_200_OK)

        self.assertEqual(changed_get.data['name'], name['name'])
