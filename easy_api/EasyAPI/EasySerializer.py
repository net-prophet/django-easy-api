from rest_framework import serializers
from rest_framework.fields import ReadOnlyField


class classproperty(object):
    def __init__(self, f):
        self.f = f

    def __get__(self, obj, owner):
        return self.f(owner)


class EasySerializable:
    @classmethod
    def get_base_serializer_class(cls, Model):

        class EasyBaseSerializer(serializers.ModelSerializer):
            def build_unknown_field(self, field_name, model_class):
                get_field = getattr(
                    model_class,
                    field_name,
                    getattr(model_class, 'get_%s' % field_name, '')
                )

                if get_field:
                    return ReadOnlyField, {}

                # Raise the default exception
                super(EasyBaseSerializer, self).build_unknown_field(
                    field_name,
                    model_class
                )

            class Meta:
                model = Model
                fields = '__all__'

        return EasyBaseSerializer

    @classmethod
    def get_serializer_class(cls):
        from rest_framework import serializers

        Klass = cls.get_base_serializer_class()

        class EasySerializer(Klass):
            dataviews = serializers.SerializerMethodField(read_only=True)

            def get_dataviews(self, obj):
                request = self.context.get('request', None)
                views = self.context.get(
                    'views',
                    getattr(request, 'GET', {}).get('views')
                )
                rendered_views = obj.get_dataviews_config()
                if views:
                    for v in views.split(','):
                        if v in rendered_views:
                            rendered_views[v]['output'] = obj.get_dataview(
                                v,
                                request
                            )
                return rendered_views

        return EasySerializer()

    @classproperty
    def serializer(cls):
        print('serializer')
        return cls.get_serializer_class()

    def serialize(self, views=None):
        print('serialize')
        return type(self).serializer(self)

    def serialized(self):
        print('serialized')
        return self.serialize().data

    @classmethod
    def get_serializer_fields(cls):
        print('')
        return cls.field_names + cls.get_serializer_methods()

    @classmethod
    def get_serializer_methods(cls):
        return []

    @classmethod
    def get_serializer_read_only_fields(cls):
        return cls.get_serializer_methods()
