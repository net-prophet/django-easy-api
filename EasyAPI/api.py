from weakref import WeakSet

import graphene
from django.apps import apps
from django.conf.urls import url
from django.contrib import admin
from django.contrib.auth.mixins import AccessMixin
from django.db.models.base import ModelBase
from graphene_django.types import DjangoObjectType
from graphene_django.views import GraphQLView
from rest_framework import permissions

all_apis = WeakSet()
actions = ["create", "edit", "retrieve", "list", "delete"]


class AlreadyRegistered(Exception):
    pass


def check_dependencies(app_configs, **kwargs):
    errors = []
    from django.core import checks

    if not apps.is_installed("EasyAPI"):
        return errors

    error = "'%s' must be in INSTALLED_APPS to use django-easy-api"

    def check_app_installed(app):
        if not apps.is_installed(app):
            missing_app = checks.Error(error % app)
            errors.append(missing_app)

    check_app_installed("django.contrib.contenttypes")
    check_app_installed("rest_framework")
    check_app_installed("django_filters")

    return errors


class EasyAPI(object):
    _registry = {}

    def __init__(
        self,
        name,
        permission,
        description=None,
        rest=True,
        graphql=True,
        admin=False,
        permission_context="*",
        dump_info=False,
    ):
        self.name = name
        self._registry = {}
        self.description = (
            description
            if description is not None
            else "API generated by Django Easy API"
        )
        self.permissions = [permission]
        self.rest = rest
        self.graphql = graphql
        self.admin = admin
        self.dump_info = dump_info
        self.permission_context = permission_context
        self._registry.update(self._registry)

    def __str__(self):
        return "<EasyAPI %s>" % self.name

    def register(self, api_resource, **kwargs):
        from .resources import ModelResource

        if isinstance(api_resource, ModelBase):
            api_resource = ModelResource.generate_for_model(api_resource, **kwargs)

        # Check to make sure we are registering ModelAPI only
        from django.core.exceptions import ImproperlyConfigured

        if not issubclass(api_resource, ModelResource):
            raise ImproperlyConfigured(
                "The model %s is not a ModelResource, so it cannot "
                "be registered with the api." % api_resource.__name__
            )

        api = api_resource(self)
        model = api_resource.Meta.model

        if model._meta.abstract:
            raise ImproperlyConfigured(
                "The model %s is abstract, so it cannot "
                "be registered with the api." % model.__name__
            )
        if model in self._registry:
            raise AlreadyRegistered(
                "The model %s is already registered." % model.__name__
            )

        self._registry[model] = api

        for name in api.inlines:
            inline = api.get_inline_model(name)
            if inline not in self._registry:
                self.register(inline)

        if self.admin:
            admin.site.register(model, api.generate_admin())

    @property
    def urls(self):
        return self.get_urls(), self.name, self.name

    def get_resource_for_model(self, model):
        return self._registry.get(model, None)

    def get_urls(self):
        from rest_framework.routers import APIRootView, DefaultRouter
        from EasyAPI.metadata import EasyAPIMetadata

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
                    permissions = kwargs["permissions"]

                return AssembledEasyAPIRootView

        router.APIRootView = EasyAPIRootView.Assemble(
            name=self.name, permissions=self.permissions
        )
        router.APIRootView.__doc__ = self.description

        queries = []
        mutations = []
        for model, resource in self._registry.items():
            resource.filterset.add_subfilters()
            if self.dump_info or resource.dump_info:
                resource.__dump_info__()
            name = model._meta.model_name

            if self.rest:
                viewset = resource.generate_viewset()
                router.register(
                    r"%s" % resource.label, viewset, "%s %s" % (name, resource.label),
                )

            if self.graphql:
                objectType, query, mutation = resource.generate_graphql()
                query and queries.append(query)
                mutation and mutations.append(mutation)

        if self.graphql:

            class Query(*queries, graphene.ObjectType):
                pass

            class Mutate(*mutations, graphene.ObjectType):
                pass

            class PermissionedGraphQL(AccessMixin, GraphQLView):
                permission_classes = self.permissions
                raise_exception = True

                def dispatch(self, request, *args, **kwargs):
                    for permission_class in self.permission_classes:
                        permission = permission_class()
                        if not permission.has_permission(request, self):
                            return self.handle_no_permission()
                    return super().dispatch(request, *args, **kwargs)

            schema = graphene.Schema(query=Query, mutation=mutations and Mutate or None)
            urlpatterns = router.urls + [
                url(
                    r"^graphql$",
                    PermissionedGraphQL.as_view(graphiql=True, schema=schema),
                ),
            ]
        return urlpatterns
