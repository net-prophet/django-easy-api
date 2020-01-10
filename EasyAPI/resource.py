
import collections
from weakref import WeakSet

import graphene
from django.apps import apps
from django.conf.urls import url
from django.contrib import admin
from django.db import models
from django.db.models.base import ModelBase
from django.db.models.fields import related, reverse_related
from graphene_django.types import DjangoObjectType
from graphene_django.views import GraphQLView
from rest_framework.permissions import AllowAny, BasePermission
from rest_framework.routers import APIRootView, DefaultRouter

from EasyAPI.metadata import EasyAPIMetadata


def get_gql_type(fields, field):
    from django.db import models
    from graphene_django.converter import convert_django_field
    if field not in fields:
        return None
    return convert_django_field(fields[field])
    
class AllowNone(BasePermission):
    def has_permission(self, request, view):
        return False

class ModelResource(object):
    description = "Generated by EasyAPI"
    permissions = [AllowAny]
    model = None
    viewset_class = None
    filterset_class = None
    graphql_query = None
    fields = []
    read_only = []
    list_display = []
    inlines = []

    def __init__(self, api,
            fields=None, # Fields that can be read and potentially edited
            read_only=None, # Fields, methods and properties that are read-only
            list_display=None, # The favorite fields to display in a table
            permissions=None,
            inlines=None,
            viewset_class=None,
            filterset_class=None,
            graphql_query=None,
        ):
        self.api = api
        self.permissions = permissions or self.permissions
        self.viewset_class = viewset_class or self.viewset_class
        self.filterset_class = filterset_class or self.filterset_class
        self.graphql_query = graphql_query or self.graphql_query
        self.fields = list(fields or self.fields or self.model_fields.keys())
        self.read_only = read_only or self.read_only
        self.list_display = list(list_display or self.list_display or self.model_fields_local.keys())
        self.inlines = inlines or self.inlines

    @classmethod
    def generate_for_model(cls, _model, **kwargs):
        class Meta(kwargs.get('Meta', object)):
            model = _model
        kwargs['Meta'] = Meta

        return type('%sResource'%_model._meta.object_name, (cls,), kwargs)

    @property
    def model(self):
        from django.core.exceptions import ImproperlyConfigured

        try:
            return self.Meta.model
        except:
            raise ImproperlyConfigured("Can't make a %s without setting Meta.model"%self)
    
    @property
    def label(self):
        return self.model._meta.verbose_name_plural.replace(' ', '_').lower()

    
    @property
    def model_fields(self):
        return collections.OrderedDict([
            (f.name, f) for f in self.model._meta.get_fields()
        ])

    @property
    def model_fields_local(self):
        return collections.OrderedDict([
            (k, v) for k, v in self.model_fields.items()
            if not isinstance(v, reverse_related.ForeignObjectRel)
        ])

    def get_inline_model(self, name):
        return self.model_fields[name].related_model

    def get_filterset_class(self):
        from EasyAPI.EasyFilters import EasyFilters
        if not self.filterset_class:
            self.filterset_class = EasyFilters.get_filter_class(
                self.model, self.fields)
        return self.filterset_class

    def get_filterset(self):
        FilterSet = self.get_filterset_class()
        return FilterSet()
    
    def get_filter_fields(self):
        return self.get_filterset().filter_fields

    def get_serializer_fields(self, exclude=None):
        return [f for f in list(self.fields)
            if f is not 'id' and f in self.model_fields
            and f not in (exclude or [])
        ] + ['pk']
        
    def get_read_only_fields(self):
        return ['pk', ] + (self.read_only or [
            f for f in list(self.fields)
            if f in self.model_fields
            and isinstance(self.model_fields[f], reverse_related.ForeignObjectRel)
        ])


    def generate_viewset(self):
        from .EasyViewSet import EasyViewSet
        return (self.viewset_class or EasyViewSet).Assemble(
            model=self.model,
            fields=self.fields,
            resource=self,
            permissions=self.permissions + self.api.permissions,
            description=self.description,
        )

    @property
    def gql_fields(self):
        fields = {field: get_gql_type(self.model_fields, field) for field in self.fields}

        return {k: v for k, v in fields.items() if v}

    def generate_graphql(self):
        from graphene_django.filter import DjangoFilterConnectionField

        if self.graphql_query:
            return self.graphql_query

        class Meta:
            model = self.model
            name = self.model._meta.object_name
            fields = list(self.gql_fields.keys())
            filter_fields = self.get_filter_fields()
            interfaces = (graphene.relay.Node,)

        EasyObjectType = type(Meta.name, (DjangoObjectType,), {
            "Meta": Meta
        })

        stub = ''.join(part.capitalize()
            for part in self.model._meta.verbose_name_plural.split(' '))
        list_view = "all_%s" % stub
        detail_view = stub

        gql_list = DjangoFilterConnectionField(EasyObjectType)
        gql_detail = graphene.relay.Node.Field(EasyObjectType)

        EasyObjectTypeQuery = type("%sQuery"%Meta.name, (object,), {
            detail_view: gql_detail,
            #"resolve_%s"%detail_view: _detail,
            list_view: gql_list,
            #"resolve_%s"%list_view: _list,
        })

        return EasyObjectType, EasyObjectTypeQuery

    def generate_admin_inline(self, inline_class=None):
        return self.generate_admin(admin_class=inline_class or admin.StackedInline)

    def generate_admin(self, admin_class=None):
        admin_class = admin_class or admin.ModelAdmin
        GeneratedAdmin = type("%sGeneratedAdmin"%self.model._meta.object_name, (admin_class,), {
            'model': self.model
        })

        if not self.list_display:
            list_display = []
            DEFAULT_FIELDS = ['created_at', 'modified_at', 'status', 'order', 'level', 'parent', 'title', 'name']
            for field in DEFAULT_FIELDS:
                if hasattr(modelKlass, field):
                    list_display.append(field)
        else:
            list_display = self.list_display

        setattr(GeneratedAdmin, 'list_display', list_display)
        
        if self.inlines and not getattr(GeneratedAdmin, 'inlines'):
            setattr(GeneratedAdmin, 'inlines', [
                self.api._registry[self.get_inline_model(i)].generate_admin_inline() for i in self.inlines
            ])

        return GeneratedAdmin