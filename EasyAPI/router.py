from .EasyViewSet import EasyViewSet
from EasyAPI.metadata import EasyAPIMetadata
from rest_framework.routers import DefaultRouter, APIRootView
from graphene_django.views import GraphQLView

import graphene
from django.conf.urls import url


def easy_router(self):
    router = DefaultRouter()

    class EasyAPIRootView(APIRootView):
        metadata_class = EasyAPIMetadata

        @classmethod
        def get_view_name(self):
            return self.name

        @classmethod
        def Assemble(cls, **kwargs):
            class AssembledEasyAPIRootView(cls):
                name = kwargs["name"]
                perms = kwargs["perms"]

            return AssembledEasyAPIRootView

    router.APIRootView = EasyAPIRootView.Assemble(
        name=self.name, perms=self.permissions
    )
    router.APIRootView.__doc__ = self.description

    queries = []
    for model, model_api in self._registry.items():
        name = model._meta.model_name
        label = model._meta.app_label
        api = model_api()
        router.register(
            r"%s" % label,
            api.generate_viewset(_model=model),
            "%s %s" % (name, label),
        )

        objectType, query = api.generate_graphql(_model=model,)
        queries.append(query)

    class Query(*queries, graphene.ObjectType):
        pass

    schema = graphene.Schema(query=Query)

    urlpatterns = router.urls + [
        url(r"^graphql$", GraphQLView.as_view(graphiql=True, schema=schema)),
    ]
    return urlpatterns
