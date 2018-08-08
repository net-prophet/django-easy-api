from rest_framework import viewsets
from rest_framework.routers import DynamicRoute, Route
from rest_framework.routers import DefaultRouter, APIRootView

from EasyAPI.EasySerializer import EasySerializable
from EasyAPI.metadata import EasyAPIMetadata


class EasyViewSet(viewsets.ModelViewSet):

    @classmethod
    def get_view_name(self):
        return self.model._meta.app_label

    @classmethod
    def kwargs(cls, **kwargs):
        class Kwargs(cls):
            fields = kwargs['fields']
            model = kwargs['model']
            model_perm = kwargs['model_perm']
            permission_classes = kwargs['api_perm']
        return Kwargs

    @classmethod
    def crud_permissions(cls, request):
        crud = []
        if request.user.is_authenticated:
            crud = ['create', 'edit', 'details', 'list', 'delete']
        return crud

    def get_queryset(self):
        model = self.model
        return model.objects.all()

    def get_serializer_class(self):
        e = EasySerializable.get_base_serializer_class(self.model())
        e.Meta.fields = self.fields
        return e

class EasyAPIRootView(APIRootView):
    metadata_class = EasyAPIMetadata

    @classmethod
    def get_view_name(self):
        return 'Name'

class EasyRouter(DefaultRouter):
    APIRootView = EasyAPIRootView
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
    # router = EasyRouter()
    router = DefaultRouter()
    for model, api in self._registry.items():
        name = model._meta.model_name
        label = model._meta.app_label
        router.register(r'%s' % label,
                        EasyViewSet.kwargs(model=model,
                                           fields=api.api_fields,
                                           model_perm=api.crud_permissions,
                                           api_perm=self.permissions,
                                           ),
                        '%s %s' % (name, label)
                        )


    urlpatterns = router.urls
    return urlpatterns
