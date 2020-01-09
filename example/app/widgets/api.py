from .models import Widget
from EasyAPI.api import ModelResource
from example.app.api import publicapi, privateapi, complexapi


class PublicWidgetAPI(ModelResource):
    api_fields = ('name', 'color')
    class Meta:
        model = Widget


class PrivateWidgetAPI(ModelResource):
    api_fields = ('name', 'color', 'size', 'shape', 'cost')
    class Meta:
        model = Widget

class ComplexWidgetAPI(ModelResource):
    api_fields = ('name', 'color', 'size', 'shape', 'cost')
    class Meta:
        model = Widget


publicapi.register(Widget, PublicWidgetAPI)
privateapi.register(Widget, PrivateWidgetAPI)
complexapi.register(Widget, ComplexWidgetAPI)
