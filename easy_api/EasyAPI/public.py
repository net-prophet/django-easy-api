from django.apps import apps
from rest_framework import serializers, viewsets
from rest_framework.routers import DynamicRoute, Route, DefaultRouter


class PublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = None
        fields = '__all__'


class PublicViewSet(viewsets.ModelViewSet):
    @property
    def model(self):
        name, label = self.basename.split()
        return apps.get_model(app_label=label, model_name=name)

    def get_queryset(self):
        model = self.model
        return model.objects.all()

    def get_serializer_class(self):
        PublicSerializer.Meta.model = self.model
        return PublicSerializer


class PublicReadOnlyRouter(DefaultRouter):
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

router = PublicReadOnlyRouter()
for model in apps.get_models():
    try:
        name = model._meta.model_name
        label = model._meta.app_label
        router.register(r'%s' % label, PublicViewSet, '%s %s' % (name, label))
    except AttributeError:
        pass

urlpatterns = router.urls

