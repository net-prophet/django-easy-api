from django.db import models

from django.apps import apps
from django.db.models.base import ModelBase
from django.conf import settings
from weakref import WeakSet

from EasyAPI.router import easy_router

all_apis = WeakSet()


class AlreadyRegistered(Exception):
    pass


class EasyAPI:
    _registry = {}

    def __init__(self, name, *args, **kwargs):
        self._registry = {}
        self.name = name
        all_apis.add(self)
        self._registry.update(self._registry)

    def check(self, app_configs):
        if app_configs is None:
            app_configs = apps.get_app_configs()
        app_configs = set(app_configs)

        errors = []
        modelapis = (o for o in self._registry.values() if o.__class__ is not
                     EasyAPI)

        for modelapi in modelapis:
            if modelapi.model._meta.app_config in app_configs:
                errors.extend(modelapi.check())

        return errors

    def check_api_app(app_configs, **kwargs):
        errors = []
        for api in all_apis:
            errors.extend(api.check(app_configs))
        return errors

    def check_dependencies(app_configs, **kwargs):
        errors = []
        from django.core import checks
        if not apps.is_installed('django.contrib.contenttypes'):
            missing_app = checks.Error(
                "'django.contrib.contenttypes' must be in INSTALLED_APPS"
                " to use django-easy-admin",
            )
            errors.append(missing_app)
        return errors

    def register(cls, model, api_class=None, **options):

        try:
            cls.verify_api(cls.name)
        except Exception as e:
            print(e)

        api_class = api_class or ModelAPI
        if isinstance(model, ModelBase):
            model = [model]

        for m in model:
            if m._meta.abstract:
                from django.core.exceptions import ImproperlyConfigured
                raise ImproperlyConfigured(
                    'The model %s is abstract, so it cannot '
                    'be registered with api.' % m.__name__
                )
            if m in cls._registry:
                raise AlreadyRegistered(
                    'The model %s is already registered' % m.__name__
                )
            cls._registry[m] = api_class

    @property
    def urls(self):
        return self.get_urls(), self.name, self.name

    def get_urls(self):

        if self.name == 'debugapi':
            from EasyAPI.public import debug_router
            return debug_router(self)

        router = easy_router(self)
        return router

    @classmethod
    def verify_api(cls, name):
        if name not in set(settings.EASYAPIS):
            raise Exception('This is not a registered EasyAPI!')


debugapi = EasyAPI('debugapi')
publicapi = EasyAPI('publicapi')
privateapi = EasyAPI('privateapi')


class ModelAPI(models.Model):
    crud = ['c', 'r', 'u', 'd']

    class Meta:
        app_label = 'EasyAPI'

    def __init__(self, model, api_fields):
        self.model = model
        self.api_fields = api_fields
        super(ModelAPI, self).__init__()
