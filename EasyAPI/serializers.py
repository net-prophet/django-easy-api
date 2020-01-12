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

        fields = (primary_key and [primary_key,] or []) + [
            f for f in resource.fields
            if f not in ['id', 'pk'] + resource.reverse_relations]
        ALL = fields
        RO = resource.read_only
        class EasyBaseSerializer(serializers.ModelSerializer):
            @classmethod
            def Assemble(_class, primary_key='pk'):
                return cls.Assemble(resource, primary_key=primary_key)
            class Meta:
                model = resource.model
                fields = ALL
                read_only_fields = RO

        return EasyBaseSerializer
