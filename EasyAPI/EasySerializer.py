from django.db.models.fields.reverse_related import ForeignObjectRel
from rest_framework import serializers


class classproperty(object):
    def __init__(self, f):
        self.f = f

    def __get__(self, obj, owner):
        return self.f(owner)


class EasySerializable(object):
    @classmethod
    def get_base_serializer_class(cls, resource):
        fields = ['pk',] + [f for f in resource.fields if f not in ['id', 'pk']]
        ALL = fields
        RO = resource.read_only
        class EasyBaseSerializer(serializers.ModelSerializer):
            class Meta:
                model = resource.model
                fields = ALL
                read_only_fields = RO

        return EasyBaseSerializer
