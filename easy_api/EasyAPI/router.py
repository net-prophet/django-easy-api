import graphene
from graphene_django.views import GraphQLView
from .EasyViewSet import EasyViewSet
from EasyAPI.metadata import EasyAPIMetadata
from rest_framework.routers import DefaultRouter, APIRootView
from django.conf.urls import url


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

    graphql_queries = []
    graphql_mutations = []

    for model, model_api in self._registry.items():
        name = model._meta.model_name
        label = model._meta.app_label
        viewset = EasyViewSet.factory(model=model,
                                      model_api=model_api,
                                      fields=model_api.api_fields,
                                      actions=model_api.permissions,
                                      description=model_api.description,
                                      )

        router.register(r'%s' % label, viewset,
                        '%s %s' % (name, label))

        query, mutation = viewset.get_graphql_query()
        if query: graphql_queries.append(query)
        if mutation: graphql_mutations.append(mutation)

    class EasyGQLQueries(*graphql_queries, graphene.ObjectType):
        pass

    class EasyGQLMutations(*graphql_mutations, graphene.ObjectType):
        pass

    schema = graphene.Schema(query=EasyGQLQueries, mutation=EasyGQLMutations)
    view = GraphQLView.as_view(graphiql=True, schema=schema)

    urlpatterns = router.urls + [
        url(r'graphql', view)
    ]
    return urlpatterns
