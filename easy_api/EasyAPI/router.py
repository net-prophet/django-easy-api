from rest_framework import viewsets
from rest_framework.routers import DynamicRoute, Route, DefaultRouter

from EasyAPI.EasySerializer import EasySerializable


class EasyViewSet(viewsets.ModelViewSet):

    @classmethod
    def custom_fields(cls, **kwargs):
        class CustomFields(cls):
            fields = kwargs['fields']
            m = kwargs['m']

        return CustomFields

    @classmethod
    def permission_classes(cls, **kwargs):
        class GetPermissions(cls):
            permission_classes = kwargs['p']

        return GetPermissions

    @property
    def model(self):
        return self.m

    @property
    def fields(self):
        return self.fields

    def get_queryset(self):
        model = self.model
        return model.objects.all()

    def get_serializer_class(self):
        e = EasySerializable.get_base_serializer_class(self.model())
        e.Meta.fields = self.fields
        return e


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
    try:
        permissions = self.permission_classes
    except AttributeError:
        from django.conf import settings
        permissions = settings.REST_FRAMEWORK
        permissions = permissions['DEFAULT_PERMISSION_CLASSES']
    router = EasyRouter()
    for model, api in self._registry.items():
        name = model._meta.model_name
        label = model._meta.app_label
        router.register(r'%s' % label,
                        EasyViewSet.custom_fields(m=model,
                                                  fields=api.api_fields
                                                  ).permission_classes(
                                                      p=permissions
                                                  ),
                        '%s %s' % (name, label)
                        )

    urlpatterns = router.urls
    return urlpatterns
