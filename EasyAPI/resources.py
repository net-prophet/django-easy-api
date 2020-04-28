import collections
from weakref import WeakSet

import graphene
from django.apps import apps
from django.conf.urls import url
from django.contrib import admin
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models
from django.db.models.base import ModelBase
from django.db.models.fields import related, reverse_related
from graphene_django.filter.fields import DjangoFilterConnectionField
from graphene_django.types import DjangoObjectType
from graphene_django.utils import get_model_fields
from graphene_django.views import GraphQLView
from rest_framework.permissions import AllowAny, BasePermission
from rest_framework.routers import APIRootView, DefaultRouter

from EasyAPI.filters import EasyFilters
from EasyAPI.metadata import EasyAPIMetadata
from EasyAPI.serializers import EasySerializable
from EasyAPI.permissions import get_action_permission, get_permitted_queryset, get_permitted_object


def get_gql_type(fields, field):
    from django.db import models
    from graphene_django.converter import convert_django_field

    if field not in fields:
        return None

    if field == "id":
        return graphene.ID
    return convert_django_field(fields[field])


class ModelResource(object):
    description = "Generated by EasyAPI"
    permissions = [AllowAny]
    model = None
    viewset_class = None
    filterset_class = None
    serializer_class = None
    admin_class = None
    properties = None
    fields = []
    read_only = []
    write_only = []
    list_display = []
    inlines = []
    dump_info = False

    def __init__(
        self,
        api,
        fields=None,  # Fields that can be read and potentially edited
        exclude=None,  # Fields that will be excluded
        read_only=None,  # Fields that are read-only
        write_only=None,  # Fields that are write-only
        properties=None,  # Dynamic views available as fields on a resource
        list_display=None,  # The favorite fields to display in a table
        permissions=None,
        inlines=None,
        viewset_class=None,
        filterset_class=None,
        serializer_class=None,
        admin_class=None,
        dump_info=False,  # Print the full resource to the console upon mounting
    ):
        # Part 1: Set attributes
        self.api = api
        self.permissions = permissions or self.permissions
        self.viewset_class = viewset_class or self.viewset_class

        # Step 2: Fields
        self.model_fields = collections.OrderedDict(get_model_fields(self.model))
        self.model_fields_simple = collections.OrderedDict(
            (f.name, f) for f in self.model._meta.fields
        )

        self.relations = self.get_model_fields(
            lambda field: isinstance(field, related.ForeignObject)
        )
        self.reverse_relations = self.get_model_fields(
            lambda field: isinstance(field, reverse_related.ForeignObjectRel)
        )
        self.many_to_many = self.get_model_fields(
            lambda field: isinstance(field, related.ManyToManyField)
        )

        self.fields = list(
            f
            for f in fields
            or self.fields
            or (
                list(self.model_fields.keys()) + self.relations + self.reverse_relations
            )
            if f != "id"
        )

        self.read_only = ["pk",] + (
            read_only
            or self.read_only
            or [f for f in self.reverse_relations if f in self.fields]
        )
        self.write_only = write_only or self.write_only or []

        self.list_display = [
            f
            for f in ["pk",]
            + list(
                list_display
                or self.list_display
                or [
                    f
                    for f in self.fields
                    if not f in self.reverse_relations and not f in self.many_to_many
                ]
            )
            if f not in self.write_only
        ]

        # Part 3: Complex setups
        self.inlines = inlines or self.inlines

        self.filterset_class = (
            filterset_class or self.filterset_class or EasyFilters.Assemble(self)
        )
        self.serializer_class = (
            serializer_class or self.serializer_class or EasySerializable.Assemble(self)
        )
        self.admin_class = admin_class or self.admin_class or admin.ModelAdmin

        self.filterset = self.filterset_class()

        self.gql_fields = {
            field: get_gql_type(self.model_fields, field)
            for field in self.fields + self.inlines + ["id",]
            if self.api.graphql and
            not isinstance(self.model_fields[field], GenericForeignKey)
            and field not in self.write_only
            and field in self.model_fields
        }

        self.properties = (
            properties
            or self.properties
            or [
                attr
                for attr, value in self.model.__dict__.items()
                if getattr(value, "_APIProperty", False)
            ]
        )
        self.property_map = {
            name: getattr(self.model, name)._APIType
            for name in self.properties
            if getattr(getattr(self.model, name, None), "_APIProperty", False)
        }

    @classmethod
    def generate_for_model(cls, _model, **kwargs):
        class Meta(kwargs.get("Meta", object)):
            model = _model

        kwargs["Meta"] = Meta
        kwargs["name"] = "%sResource" % _model._meta.object_name

        return type(kwargs["name"], (cls,), kwargs)

    @property
    def model(self):
        from django.core.exceptions import ImproperlyConfigured

        try:
            return self.Meta.model
        except:
            raise ImproperlyConfigured(
                "Can't make a %s without setting Meta.model" % self
            )

    @property
    def label(self):
        return self.model._meta.verbose_name_plural.replace(" ", "_").lower()

    def get_inline_model(self, name):
        return self.model_fields[name].related_model

    def get_model_fields(self, match=None):
        return [
            name
            for name, field in self.model_fields.items()
            if not match or match(field)
        ]

    def get_permission_context(self):
        return self.api.permission_context
    

    def get_action_permission(self, action, user=None):
        return get_action_permission(self, action, user=user)

    def get_permitted_object(self, id, action, user=None, qs=None):
        return get_permitted_object(self, id, action, user=user, qs=qs)

    def get_permitted_queryset(self, action, user=None, qs=None):
        return get_permitted_queryset(self, action, user=user, qs=qs)

    def generate_viewset(self):
        from .views import EasyViewSet

        return (self.viewset_class or EasyViewSet).Assemble(
            model=self.model,
            fields=self.fields,
            resource=self,
            permissions=self.permissions + self.api.permissions,
            description=self.description,
            serializer_class=self.serializer_class,
        )

    def generate_graphql(self):
        from . import graphql

        return graphql.Assemble(self)

    def generate_admin_inline(self, name, inline_class=None):
        field = self.model_fields[name]
        related_model = self.api._registry[self.get_inline_model(name)]
        return related_model.generate_admin(
            admin_class=inline_class or admin.StackedInline,
            fk_name=field.remote_field.name,
        )

    def generate_admin(self, admin_class=None, **extra):
        admin_class = admin_class or self.admin_class
        GeneratedAdmin = type(
            "%sGeneratedAdmin" % self.model._meta.object_name,
            (admin_class,),
            {
                "model": self.model,
                "list_display": [
                    f
                    for f in self.list_display
                    if f not in self.reverse_relations and f not in self.many_to_many
                ],
                **extra,
            },
        )

        if self.inlines and not getattr(GeneratedAdmin, "inlines"):
            setattr(
                GeneratedAdmin,
                "inlines",
                [self.generate_admin_inline(i) for i in self.inlines],
            )

        return GeneratedAdmin

    def __dump_info__(self):
        print("API Resource: ", self)
        print("\tAPI:        ", self.api)
        print()
        print("\tModel:      ", self.model)
        print("\tModelFields:", list(self.model_fields.keys()))
        print("\tSimple:     ", list(self.model_fields_simple.keys()))
        print()
        print("\tFields:     ", self.fields)
        print("\tReadOnly:   ", self.read_only)
        print("\tListDisplay:", self.list_display)
        print("\tGQLFields:  ", list(self.gql_fields.keys()))

        print()
        print("\tRelations:  ", self.relations)
        print("\tReversRels: ", self.reverse_relations)
        print("\tManyToMany: ", self.many_to_many)
        print()
        print("\tInlines:    ", self.inlines)
        print("\tProperties: ", self.properties)
