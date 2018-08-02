from django.apps import apps
from rest_framework import viewsets
from rest_framework.routers import DynamicRoute, Route, DefaultRouter

from EasyAPI.EasySerializer import EasySerializable


class EasyViewSet(viewsets.ModelViewSet):
    @property
    def model(self):
        name, label = self.basename.split()
        return apps.get_model(app_label=label, model_name=name)

    def get_queryset(self):
        model = self.model
        return model.objects.all()

    def get_serializer_class(self):
        e = EasySerializable
        return e.get_base_serializer_class(self.model())


class EasyRouter(DefaultRouter):
    routes = [
        Route(
            url=r'^{prefix}/$',
            mapping={'get': 'list'},
            name='{basename}-list',
            detail=False,
            initkwargs={'suffix': 'List'}
        ),
        Route(
            url=r'^{prefix}/{lookup}$',
            mapping={'get': 'retrieve'},
            name='{basename}-detail',
            detail=True,
            initkwargs={'suffix': 'Detail'}
        ),
        DynamicRoute(
            url=r'^{prefix}/{lookup}/{url_path}$',
            name='{basename}-{url_name}',
            detail=True,
            initkwargs={}
        )
    ]


def easy_router(self):
    router = EasyRouter()
    for model, api in self._registry.items():
        name = model._meta.model_name
        label = model._meta.app_label
        router.register(r'%s' % label, EasyViewSet, '%s %s' % (name, label))

    urlpatterns = router.urls
    return urlpatterns


