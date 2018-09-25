from rest_framework import serializers


class classproperty(object):
    def __init__(self, f):
        self.f = f

    def __get__(self, obj, owner):
        return self.f(owner)


class EasySerializable(object):
    @classmethod
    def get_base_serializer_class(cls, the_model, the_fields):
        the_fields = the_fields + ('pk',)

        class EasyBaseSerializer(serializers.ModelSerializer):

            class Meta:
                model = the_model
                fields = the_fields

        return EasyBaseSerializer
