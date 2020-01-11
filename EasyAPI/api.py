from weakref import WeakSet

import graphene
from django.apps import apps
from django.conf.urls import url
from django.contrib import admin
from django.db.models.base import ModelBase
from graphene_django.types import DjangoObjectType
from graphene_django.views import GraphQLView
from rest_framework import permissions
from rest_framework.routers import APIRootView, DefaultRouter

from EasyAPI.metadata import EasyAPIMetadata

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

    def __init__(self, name, permission, description=None, 
            rest=True,
            graphql=True,
            admin=False):
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
        all_apis.add(self)
        self._registry.update(self._registry)

    def register(self, api_resource, **kwargs):
        from .resource import ModelResource
        
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

    def get_urls(self):
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
        for model, resource in self._registry.items():
            name = model._meta.model_name
            viewset = resource.generate_viewset()
            router.register(
                r"%s" % resource.label, viewset, "%s %s" % (name, resource.label),
            )

            objectType, query = resource.generate_graphql()
            queries.append(query)

        class Query(*queries, graphene.ObjectType):
            pass

        schema = graphene.Schema(query=Query)

        urlpatterns = router.urls + [
            url(r"^graphql$", GraphQLView.as_view(graphiql=True, schema=schema)),
        ]
        return urlpatterns
