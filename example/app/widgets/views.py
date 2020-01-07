from .models import Widget
from rest_framework import serializers, viewsets


class WidgetSerializer(serializers.ModelSerializer):

    class Meta:
        model = Widget
        fields = ('name', 'color', 'size', 'shape', 'cost')


class WidgetViewSet(viewsets.ModelViewSet):
    queryset = Widget.objects.all()
    serializer_class = WidgetSerializer
