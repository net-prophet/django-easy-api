import graphene
from django_filters.rest_framework import DjangoFilterBackend
from graphene_django import DjangoObjectType
from graphene_django.filter.fields import DjangoFilterConnectionField
from graphene_django.rest_framework.mutation import SerializerMutation
from rest_framework import status, viewsets
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response

from EasyAPI.metadata import EasyAPIMetadata
from EasyAPI.serializers import classproperty


def Assemble(resource):
    class ObjectMeta:
        model = resource.model
        name = resource.model._meta.object_name
        fields = list(resource.gql_fields.keys())
        filter_fields = resource.filterset.filter_fields
        interfaces = (graphene.relay.Node,)
        convert_choices_to_enum = False

    resolvers = {}
    for name, _type in resource.property_map.items():

        def get_property(name):
            def property_resolver(obj, info):
                return getattr(obj, name)()

            return property_resolver

        resolvers[name] = _type(resolver=get_property(name))

    @classmethod
    def get_queryset(cls, queryset, info):
        qs, audit = resource.get_permitted_queryset(
            "list",
            user=(info.context.user.is_authenticated and info.context.user or None),
            qs=queryset,
        )
        return qs

    @classmethod
    def get_node(cls, info, id):
        obj, audit = resource.get_permitted_object(
            id,
            "detail",
            user=(info.context.user.is_authenticated and info.context.user or None),
        )
        return obj

    ObjectType = type(
        ObjectMeta.name,
        (DjangoObjectType,),
        {
            "Meta": ObjectMeta,
            **resolvers,
            "get_queryset": get_queryset,
            "get_node": get_node,
        },
    )

    class MutationMeta:
        serializer_class = resource.serializer_class.Assemble(resource, "id")
        model = resource.model
        name = "%sMutation" % resource.model._meta.object_name
        fields = list(resource.gql_fields.keys())
        convert_choices_to_enum = False

    Mutation = type(MutationMeta.name, (SerializerMutation,), {"Meta": MutationMeta})

    stub = "".join(
        part.capitalize() for part in resource.model._meta.verbose_name.split(" ")
    )
    plural = "".join(
        part.capitalize()
        for part in resource.model._meta.verbose_name_plural.split(" ")
    )

    list_view = "all_%s" % plural
    detail_view = stub

    gql_list = DjangoFilterConnectionField(ObjectType)
    gql_detail = graphene.relay.Node.Field(ObjectType)

    EasyQuery = type(
        "%sQuery" % ObjectMeta.name,
        (object,),
        {detail_view: gql_detail, list_view: gql_list},
    )

    EasyMutations = type(
        "%sMutations" % ObjectMeta.name,
        (object,),
        {"create_%s" % stub: Mutation.Field()},
    )

    return ObjectType, EasyQuery, EasyMutations
