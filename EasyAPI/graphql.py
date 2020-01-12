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

    resolvers = dict(
        [
            ("resolve_%s" % name, lambda obj, info: getattr(obj, name)(info.context))
            for name in resource.properties
        ]
    )

    ObjectType = type(
        ObjectMeta.name, (DjangoObjectType,), {"Meta": ObjectMeta, **resolvers, **resource.property_map}
    )

    class MutationMeta:
        serializer_class = resource.serializer_class.Assemble("id")
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

    return ObjectType, EasyQuery, None and EasyMutations
