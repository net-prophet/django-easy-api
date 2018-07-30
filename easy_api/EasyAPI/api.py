from django.apps import apps
from django.db.models.base import ModelBase
from django.conf import settings
from django.conf.urls import url, include
from weakref import WeakSet

from rest_framework import serializers, viewsets


all_apis = WeakSet()

class AlreadyRegistered(Exception):
    pass

class NotRegistered(Exception):
    pass


class EasyAPI:
    _registry = {}

    def __init__(self, name='EasyAPI', *args, **kwargs):
        self._registry = {}
        print('CATCH THESE HANDS', dir(self))
        self.name = name
        print('All APIS', all_apis)
        all_apis.add(self)
        super(EasyAPI, self).__init__(*args, **kwargs)
        self._registry.update(api._registry)

    def check_api_app(self, app_configs):
        print('IN CHECK BRAH', self)
        if app_configs is None:
            app_configs = apps.get_app_configs()
        app_configs = set(app_configs)

    @property
    def urls(self):
        print('IN URLS BURLS RAH')
        class WidgetSerializer(serializers.ModelSerializer):
            class Meta:
                from widgets.models import Widget
                model = Widget
                fields = ('name', 'color', 'size', 'shape', 'cost')

        class WidgetViewSet(viewsets.ModelViewSet):
            import django
            django.setup()
            from widgets.models import Widget
            queryset = Widget.objects.all()
            serializer_class = WidgetSerializer
        return self.get_urls(), WidgetViewSet, self.name

    def get_urls(self):
        print('GET THESE URLS')
        urlpatterns = [ url(r'^test', include('EasyAPI.urls')) ]
        return urlpatterns

    @classmethod
    def verify_api(cls):
        print('verify??', dir(cls))
        if api not in set(settings.EASYAPIS):
            raise Exception('This is not a registered EasyAPI!')

    def register(cls, model, **options):
        print('all apis', all_apis, '\n')
        print('cls', cls, '\n')
        print('cls', dir(cls), '\n')
        print('model', model, '\n')
        print('options', options, '\n')
        try:
            cls.verify_api(cls)
        except Exception as e:
            print(e)

        if isinstance(model, ModelBase):
            model = [model]

        for m in model:
            print('cls: ', dir(cls))
            print('model: ', m)
            '''
            if model in cls._registry:
                raise AlreadyRegistered(
                    'The api %s is already registered' % model.__name__
                )
            '''

from django.utils.functional import LazyObject
from django.utils.module_loading import import_string
class DefaultAPI(LazyObject):
    def _setup(self):
        APIClass = import_string(apps.get_app_config('api').default_api)
        print('do we setup APIClass?', dir(APIClass))
        print('do we setup?', APIClass._registry)
        self._wrapped = APIClass()
        self._registry.update(api._registry)
        all_apis.add(self)


api = DefaultAPI()
