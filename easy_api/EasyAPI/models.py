from django.apps import apps
from django.db.models.base import ModelBase
from django.conf import settings
from weakref import WeakSet

from EasyAPI.router import easy_router
from rest_framework import permissions

all_apis = WeakSet()


class AlreadyRegistered(Exception):
    pass


class EasyAPI(object):
    _registry = {}

    def __init__(self, name, permissions, *args, **kwargs):
        self._registry = {}
        self.name = name
        self.permissions = permissions
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
        errors = [] # TODO if ModelAPI isn't models.Model then this fails
        return errors
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

    def register(cls, model, api_class, **options):

        try:
            cls.verify_api(cls.name)
        except Exception as e:
            print(e)

        api_class = api_class or ModelAPI
        if isinstance(model, ModelBase):
            model = [model]

        perm = cls.create_model_perms(api_class)
        api_class.crud_permissions = perm

        for m in model:
            if m._meta.abstract:
                from django.core.exceptions import ImproperlyConfigured
                raise ImproperlyConfigured(
                    'The model %s is abstract, so it cannot '
                    'be registered with api.' % m.__name__
                )
            if m in cls._registry:
                raise AlreadyRegistered(
                    'The model %s is already registered.' % m.__name__
                )
            cls._registry[m] = api_class

    def create_model_perms(cls, api_class):
        crud = api_class.crud_permissions
        perm_names = ('list', 'details', 'edit', 'create', 'delete')
        for k, v in crud.items():
            if k not in perm_names:
                error = "'%s' is not a valid permission name. " % k
                error += 'Valid names are %s' % str(perm_names)
                raise NameError(error)
        return {x: cls.permissions if x not in crud else crud[x] for x in perm_names}


    @property
    def urls(self):
        return self.get_urls(), self.name, self.name

    def get_urls(self):
        from EasyAPI.common_routers import common_router

        if self.name == 'debugapi' or self.name == 'adminapi':
            return common_router(self)

        return easy_router(self)

    @classmethod
    def verify_api(cls, name):
        if name not in set(settings.EASYAPIS):
            raise Exception('This is not a registered EasyAPI!')


publicapi = EasyAPI('publicapi',
                    (permissions.AllowAny,)
                    )
privateapi = EasyAPI('privateapi',
                     (permissions.IsAuthenticated,)
                     )
debugapi = EasyAPI('debugapi',
                   (permissions.AllowAny,)
                   )
adminapi = EasyAPI('adminapi',
                   (permissions.IsAdminUser,)
                   )


class ModelAPI(object):

    crud_permissions = {
        'list': (permissions.AllowAny,),
        'details': (permissions.AllowAny,),
        'edit': (permissions.AllowAny,),
        'create': (permissions.AllowAny,),
        'delete': (permissions.AllowAny,)
    }

    class Meta:
        app_label = 'EasyAPI'

    def __init__(self, model, api_fields):
        self.model = model
        self.api_fields = api_fields
        super(ModelAPI, self).__init__()
