from django.apps import apps
from rest_framework import serializers, viewsets
from rest_framework.routers import DefaultRouter


class CommonSerializer(serializers.ModelSerializer):

    class Meta:
        model = None
        fields = '__all__'


class CommonViewSet(viewsets.ModelViewSet):

    @classmethod
    def permission_classes(cls, **kwargs):
        class GetPermissions(cls):
            permission_classes = kwargs['p']

        return GetPermissions

    @property
    def model(self):
        name, label = self.basename.split()
        return apps.get_model(app_label=label, model_name=name)

    def get_queryset(self):
        model = self.model
        return model.objects.all()

    def get_serializer_class(self):
        CommonSerializer.Meta.model = self.model
        return CommonSerializer


def common_router(self):
    router = DefaultRouter()
    for model in apps.get_models():
        try:
            name = model._meta.model_name
            label = model._meta.app_label
            router.register(r'%s' % label,
                            CommonViewSet.permission_classes(
                                p=self.permissions
                            ),
                            '%s %s' % (name, label))
        except AttributeError:
            pass

    urlpatterns = router.urls
    return urlpatterns
