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
        ALL = resource.get_serializer_fields()
        RO = resource.get_read_only_fields()
        class EasyBaseSerializer(serializers.ModelSerializer):
            class Meta:
                model = resource.model
                fields = ALL
                read_only_fields = RO

        return EasyBaseSerializer
