from .EasyViewSet import EasyViewSet
from EasyAPI.metadata import EasyAPIMetadata
from rest_framework.routers import DefaultRouter, APIRootView


def easy_router(self):
    router = DefaultRouter()

    class EasyAPIRootView(APIRootView):
        metadata_class = EasyAPIMetadata

        @classmethod
        def get_view_name(self):
            return self.name

        @classmethod
        def kwargs(cls, **kwargs):
            class Kwargs(cls):
                name = kwargs['name']
                perms = kwargs['perms']
            return Kwargs

    router.APIRootView = EasyAPIRootView.kwargs(name=self.name,
                                                perms=self.permissions)
    router.APIRootView.__doc__ = self.description

    for model, model_api in self._registry.items():
        name = model._meta.model_name
        label = model._meta.app_label
        router.register(r'%s' % label,
                        EasyViewSet.kwargs(model=model,
                                           fields=model_api.api_fields,
                                           actions=model_api.permissions,
                                           description=model_api.description,
                                           ),
                        '%s %s' % (name, label)
                        )

    urlpatterns = router.urls
    return urlpatterns
