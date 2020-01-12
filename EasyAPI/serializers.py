from django.db.models.fields.reverse_related import ForeignObjectRel
from rest_framework import serializers


class classproperty(object):
    def __init__(self, f):
        self.f = f

    def __get__(self, obj, owner):
        return self.f(owner)


class EasySerializable(object):
    @classmethod
    def Assemble(cls, resource, primary_key='pk'):

        # The Resource uses this serializer for both DRF and GQL
        # so we need to omit both PK and ID, and allow one ID to be added back in
        fields = (primary_key and [primary_key,] or []) + [
            f for f in resource.fields
            if f not in ['id', 'pk'] + resource.reverse_relations]
        ALL = fields
        RO = resource.read_only

        class EasyBaseSerializer(cls, serializers.ModelSerializer):
            class Meta:
                model = resource.model
                fields = ALL
                read_only_fields = RO

        return EasyBaseSerializer
